"""Single scene rendering with Ken Burns zoom effect."""

from __future__ import annotations

import subprocess
from pathlib import Path

from comicvid.audio import reencode_audio
from comicvid.types import Config


def build_scene_video(
    clip_path: Path,
    img_path: Path,
    audio_path: Path | None,
    duration: float,
    config: Config,
    scene_label: str = "",
) -> bool:
    """Build a single scene video clip with Ken Burns zoom.

    Applies:
    - Ken Burns zoom (100% → 100%+zoom) via zoompan filter
    - Centered crop to maintain aspect ratio
    - Audio at config sample rate

    Args:
        clip_path: Output MP4 path for this scene.
        img_path: Input image path.
        audio_path: Optional audio file path.
        duration: Clip duration in seconds.
        config: Render configuration.
        scene_label: Label for logging.

    Returns:
        True on success.
    """
    frames = int(duration * config.fps)
    zoom_expr = f"1+{config.ken_burns_zoom}*on/{frames}"

    has_audio = audio_path is not None and audio_path.exists()
    aac_temp: Path | None = None

    if has_audio:
        aac_temp = clip_path.with_suffix(".aac")
        if not reencode_audio(
            audio_path,  # type: ignore[arg-type]
            aac_temp,
            config.ffmpeg,
            config.audio_sample_rate,
            config.audio_bitrate,
        ):
            return False

        cmd = [
            config.ffmpeg, "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-i", str(aac_temp),
            "-vf",
            f"scale={config.resolution}:force_original_aspect_ratio=increase,"
            f"crop={config.resolution},"
            f"zoompan=z='{zoom_expr}':d={frames}:s={config.resolution_x}:fps={config.fps}",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", str(config.crf),
            "-maxrate", config.video_bitrate,
            "-bufsize", "3000k",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            "-shortest",
            "-t", str(duration),
            str(clip_path),
        ]
    else:
        cmd = [
            config.ffmpeg, "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-vf",
            f"scale={config.resolution}:force_original_aspect_ratio=increase,"
            f"crop={config.resolution},"
            f"zoompan=z='{zoom_expr}':d={frames}:s={config.resolution_x}:fps={config.fps}",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", str(config.crf),
            "-maxrate", config.video_bitrate,
            "-bufsize", "3000k",
            "-pix_fmt", "yuv420p",
            "-an",
            "-t", str(duration),
            str(clip_path),
        ]

    label = scene_label or clip_path.stem
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [{label}] FAILED: {result.stderr[-800:]}")
        return False

    if has_audio and aac_temp is not None:
        try:
            aac_temp.unlink(missing_ok=True)
        except OSError:
            pass

    return True
