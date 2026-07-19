"""Orchestration: scene building, concatenation, subtitle burn-in, verification."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from comicvid.types import Config
from comicvid.render import build_scene_video
from comicvid.subtitle import write_ass, write_srt


def _log(msg: str) -> None:
    print(f"[comicvid] {msg}", flush=True)


def _run_cmd(cmd: list[str], desc: str = "") -> bool:
    """Run a command, return True on success, print error on failure."""
    _log(f"→ {desc or 'run'}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        _log(f"  ✗ FAILED:")
        _log(result.stderr[-2000:] if result.stderr else result.stdout[-2000:])
        return False
    tail = [l for l in result.stderr.split("\n") if l.strip()][-3:]
    for line in tail:
        _log(f"  {line}")
    return True


def resolve_image_list(image_dir: Path) -> list[Path]:
    """Get sorted list of images from directory.

    Supports: .png, .jpg, .jpeg, .webp, .bmp
    """
    extensions = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    images = sorted(
        p for p in image_dir.iterdir()
        if p.suffix.lower() in extensions
    )
    return images


def render_video(config: Config) -> dict | None:
    """Render video from images in config.image_dir.

    Pipeline:
    1. Resolve image list and durations
    2. Build each scene (Ken Burns + audio)
    3. Create subtitle file
    4. Concatenate scenes
    5. Burn subtitles
    6. Verify output

    Args:
        config: Render configuration.

    Returns:
        Report dict with metadata, or None on failure.
    """
    _log("=" * 60)
    _log("comicvid — Render")
    _log("=" * 60)

    images = resolve_image_list(config.image_dir)
    if not images:
        _log("✗ No images found in " + str(config.image_dir))
        return None

    _log(f"Found {len(images)} images")

    # ── Determine durations ──
    if config.duration is not None:
        # Spread total duration across images
        per_image = config.duration / len(images)
        durations = [per_image] * len(images)
    else:
        durations = [config.per_image_duration] * len(images)

    # ── Create temp directory ──
    temp_dir = config.temp_dir
    scenes_dir = temp_dir / "scenes"
    temp_dir.mkdir(parents=True, exist_ok=True)
    scenes_dir.mkdir(exist_ok=True)
    config.output.parent.mkdir(parents=True, exist_ok=True)

    # ── Phase 1: Build scenes ──
    _log(f"\n── Phase 1: Build {len(images)} scene(s) ──")
    clip_paths: list[Path] = []
    for i, (img_path, dur) in enumerate(zip(images, durations)):
        clip = scenes_dir / f"scene_{i:04d}.mp4"
        label = f"img_{i:04d}"
        _log(f"  Building {label} ({img_path.name}, {dur:.1f}s) ...")
        if build_scene_video(clip, img_path, config.audio, dur, config, label):
            clip_paths.append(clip)
            size_kb = clip.stat().st_size / 1024 if clip.exists() else 0
            _log(f"  ✓ {label}: {size_kb:.0f} KB")
        else:
            _log(f"  ✗ {label}: failed")
            return None

    # ── Phase 2: Create subtitles ──
    _log(f"\n── Phase 2: Create Subtitles ──")
    sub_texts: list[str] = []
    if config.subtitles:
        sub_texts = config.subtitles
    elif config.subtitle and config.subtitle.exists():
        # Read external subtitle file and convert to per-image mapping
        sub_texts = _parse_external_subtitle(config.subtitle, len(images))
    else:
        sub_texts = [""] * len(images)

    sub_path: Path | None = None
    if any(t for t in sub_texts[:len(images)]):
        if config.subtitle_format == "ass":
            sub_path = temp_dir / "subtitles.ass"
            write_ass(sub_path, durations, sub_texts[:len(images)],
                       config.width, config.height)
        else:
            sub_path = temp_dir / "subtitles.srt"
            write_srt(sub_path, durations, sub_texts[:len(images)])
        _log(f"  {sub_path.name}: {sum(1 for t in sub_texts if t)} entries")

    # ── Phase 3: Concatenate ──
    _log(f"\n── Phase 3: Concatenate ──")
    concat_file = temp_dir / "concat.txt"
    with open(concat_file, "w") as f:
        for clip in clip_paths:
            f.write(f"file '{clip.absolute()}'\n")

    concat_temp = temp_dir / "concat_output.mp4"
    cmd_concat = [
        config.ffmpeg, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(concat_temp),
    ]
    if not _run_cmd(cmd_concat, "Concatenate scenes"):
        return None

    # ── Phase 4: Burn subtitles ──
    _log(f"\n── Phase 4: Burn Subtitles ──")
    if sub_path and sub_path.exists():
        if config.subtitle_format == "ass":
            filter_expr = f"ass={sub_path}"
        else:
            filter_expr = f"subtitles={sub_path}"

        cmd_sub = [
            config.ffmpeg, "-y",
            "-i", str(concat_temp),
            "-vf", filter_expr,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", str(config.crf),
            "-maxrate", config.video_bitrate,
            "-bufsize", "3000k",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            str(config.output),
        ]
        if not _run_cmd(cmd_sub, f"Burn subtitles ({config.subtitle_format.upper()})"):
            return None
    else:
        shutil.copy2(concat_temp, config.output)
        _log("  (no subtitles to burn)")

    # ── Phase 5: Verify ──
    _log(f"\n── Phase 5: Verification ──")
    info = verify_video(config.output, config.ffmpeg)
    _log(f"  Output:  {info['path']}")
    _log(f"  Size:    {info['size_mb']:.2f} MB")
    _log(f"  Dur:     {info.get('duration', 'N/A')}")
    _log(f"  Video:   {info.get('video', 'N/A')}")
    _log(f"  Audio:   {info.get('audio', 'N/A')}")

    if info["passes"]:
        _log(f"\n{'='*60}")
        _log(f"✓ Render complete: {config.output}")
        _log(f"{'='*60}")
        info["status"] = "ok"
    else:
        _log(f"\n⚠ Output < 1 MB. Check manually.")
        info["status"] = "small_output"

    # ── Cleanup ──
    if not config.keep_temps:
        _log("  Cleaning up temp files...")
        shutil.rmtree(temp_dir, ignore_errors=True)

    return info


def verify_video(video_path: Path, ffmpeg: str = "ffmpeg") -> dict:
    """Extract metadata from output video using ffmpeg."""
    result = subprocess.run(
        [ffmpeg, "-i", str(video_path), "-hide_banner"],
        capture_output=True, text=True,
    )
    info: dict = {
        "path": str(video_path),
        "size_bytes": video_path.stat().st_size,
        "size_mb": video_path.stat().st_size / (1024 * 1024),
    }
    for line in result.stderr.split("\n"):
        if "Duration" in line:
            info["duration"] = line.strip().split(",")[0].split("Duration:")[-1].strip()
        if "Stream #0:0" in line and "Video" in line:
            info["video"] = line.strip()
        if "Stream #0:1" in line and "Audio" in line:
            info["audio"] = line.strip()
        if "bitrate" in line and "kb/s" in line:
            parts = line.strip().split(",")
            for p in parts:
                if "kb/s" in p:
                    info["bitrate"] = p.strip()

    info["passes"] = info.get("size_mb", 0) > 0
    return info


def write_report(report: dict, path: Path) -> None:
    """Write render report as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def _parse_external_subtitle(sub_path: Path, num_images: int) -> list[str]:
    """Parse an external SRT/ASS file into per-image subtitle mapping.

    For simplicity, returns all non-empty lines as one subtitle per image.
    More sophisticated parsing would use the SRT/ASS timing, but since
    we divide time equally per image, we just map line-by-line.
    """
    content = sub_path.read_text(encoding="utf-8")
    # Remove ASS headers/formatting
    if sub_path.suffix.lower() == ".ass":
        lines = []
        in_events = False
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped == "[Events]":
                in_events = True
                continue
            if in_events and stripped.startswith("Dialogue:"):
                # Extract text after last comma
                parts = stripped.split(",", 9)
                if len(parts) >= 10:
                    lines.append(parts[9])
        return (lines + [""] * num_images)[:num_images]
    else:
        # SRT: extract text between timestamps
        lines = []
        for block in content.strip().split("\n\n"):
            parts = block.split("\n", 2)
            if len(parts) >= 3:
                lines.append(parts[2])
        return (lines + [""] * num_images)[:num_images]
