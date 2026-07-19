"""Click CLI entry point for comicvid."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from comicvid import __version__
from comicvid.pipeline import render_video
from comicvid.types import Config


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="comicvid")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """comicvid — Static images to animated video.

    Turn a folder of images into a video with Ken Burns zoom,
    ASS subtitles, and audio sync. Pure FFmpeg + Python.
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.argument("image_dir", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("-o", "--output", default="output.mp4", show_default=True,
              help="Output MP4 path.")
@click.option("--duration", type=float, default=None,
              help="Total video duration in seconds. If omitted, "
                   "uses --per-image-duration per image.")
@click.option("--per-image-duration", type=float, default=3.0, show_default=True,
              help="Seconds per image when --duration is not set.")
@click.option("--subtitle", type=click.Path(exists=True, dir_okay=False),
              default=None,
              help="External subtitle file (SRT or ASS).")
@click.option("--subtitle-format", type=click.Choice(["ass", "srt"]),
              default="ass", show_default=True,
              help="Subtitle format.")
@click.option("--text", "-t", multiple=True,
              help="Subtitle text per image. Repeat for each image: "
                   "-t 'line1' -t 'line2'")
@click.option("--audio", type=click.Path(exists=True, dir_okay=False),
              default=None, help="Audio file (WAV, MP3, etc.).")
@click.option("--width", type=int, default=1280, show_default=True,
              help="Output video width in pixels.")
@click.option("--height", type=int, default=720, show_default=True,
              help="Output video height in pixels.")
@click.option("--resolution", type=str, default=None,
              help="Shortcut: '1920x1080' sets width and height at once.")
@click.option("--fps", type=int, default=24, show_default=True,
              help="Frames per second.")
@click.option("--crf", type=int, default=23, show_default=True,
              help="H.264 CRF quality (lower = better).")
@click.option("--video-bitrate", default="1500k", show_default=True,
              help="Video bitrate.")
@click.option("--zoom", type=float, default=0.05, show_default=True,
              help="Ken Burns zoom amount (0.05 = 5%%).")
@click.option("--ffmpeg", default="ffmpeg", show_default=True,
              help="FFmpeg binary path.")
@click.option("--keep-temps", is_flag=True, default=False,
              help="Keep temporary files.")
def render(
    image_dir: str,
    output: str,
    duration: float | None,
    per_image_duration: float,
    subtitle: str | None,
    subtitle_format: str,
    text: tuple[str, ...],
    audio: str | None,
    width: int,
    height: int,
    resolution: str | None,
    fps: int,
    crf: int,
    video_bitrate: str,
    zoom: float,
    ffmpeg: str,
    keep_temps: bool,
) -> None:
    """Render images from IMAGE_DIR into an MP4 video.

    IMAGE_DIR should contain panel images sorted by filename.
    Supports PNG, JPG, JPEG, WEBP, BMP.
    """
    # Handle --resolution shortcut
    if resolution:
        try:
            w, h = resolution.split("x")
            width = int(w)
            height = int(h)
        except (ValueError, TypeError):
            click.echo(f"Error: Invalid resolution format '{resolution}'. "
                       f"Use WxH (e.g. 1920x1080).", err=True)
            sys.exit(1)

    # Parse subtitle texts
    subs: list[str] | None = list(text) if text else None

    config = Config(
        image_dir=Path(image_dir),
        output=Path(output),
        duration=duration,
        per_image_duration=per_image_duration,
        subtitle=Path(subtitle) if subtitle else None,
        subtitle_format=subtitle_format,
        subtitles=subs,
        audio=Path(audio) if audio else None,
        width=width,
        height=height,
        fps=fps,
        crf=crf,
        video_bitrate=video_bitrate,
        ken_burns_zoom=zoom,
        ffmpeg=ffmpeg,
        keep_temps=keep_temps,
    )

    report = render_video(config)
    if report is None:
        sys.exit(1)
    if report.get("status") != "ok":
        sys.exit(1)


@cli.command()
@click.argument("parent_dir", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("-o", "--output-dir", default="./output", show_default=True,
              help="Output directory for batch renders.")
@click.option("--duration", type=float, default=None,
              help="Total video duration per subfolder.")
@click.option("--per-image-duration", type=float, default=3.0, show_default=True,
              help="Seconds per image when --duration is not set.")
@click.option("--subtitle-format", type=click.Choice(["ass", "srt"]),
              default="ass", show_default=True)
@click.option("--audio", type=click.Path(exists=True, dir_okay=False),
              default=None, help="Optional audio file for all batches.")
@click.option("--width", type=int, default=1280, show_default=True)
@click.option("--height", type=int, default=720, show_default=True)
@click.option("--resolution", type=str, default=None)
@click.option("--ffmpeg", default="ffmpeg", show_default=True)
@click.option("--keep-temps", is_flag=True, default=False)
def batch(
    parent_dir: str,
    output_dir: str,
    duration: float | None,
    per_image_duration: float,
    subtitle_format: str,
    audio: str | None,
    width: int,
    height: int,
    resolution: str | None,
    ffmpeg: str,
    keep_temps: bool,
) -> None:
    """Batch render: process each subfolder in PARENT_DIR as a separate video.

    Useful for episode directories where each subfolder contains panels.
    Output files are named after each subfolder.
    """
    if resolution:
        try:
            w, h = resolution.split("x")
            width = int(w)
            height = int(h)
        except (ValueError, TypeError):
            click.echo(f"Error: Invalid resolution '{resolution}'.", err=True)
            sys.exit(1)

    parent = Path(parent_dir)
    subdirs = sorted(d for d in parent.iterdir() if d.is_dir())

    if not subdirs:
        click.echo(f"No subdirectories found in {parent_dir}")
        sys.exit(1)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    success = 0
    failed = 0

    for subdir in subdirs:
        click.echo(f"\n{'='*60}")
        click.echo(f"Batch: {subdir.name}")
        click.echo(f"{'='*60}")

        # Look for audio_* files in the subfolder or parent
        audio_path = None
        if audio:
            audio_path = Path(audio)
        else:
            # Auto-discover audio files
            audio_files = sorted(
                p for p in subdir.iterdir()
                if p.suffix.lower() in {".wav", ".mp3", ".m4a", ".aac", ".flac"}
            )
            if audio_files:
                audio_path = audio_files[0]

        # Look for subtitle files
        sub_files = sorted(
            p for p in subdir.iterdir()
            if p.suffix.lower() in {".srt", ".ass"}
        )
        sub_path = sub_files[0] if sub_files else None

        config = Config(
            image_dir=subdir,
            output=out_dir / f"{subdir.name}.mp4",
            duration=duration,
            per_image_duration=per_image_duration,
            subtitle=sub_path,
            subtitle_format=subtitle_format,
            audio=audio_path,
            width=width,
            height=height,
            ffmpeg=ffmpeg,
            keep_temps=keep_temps,
        )

        report = render_video(config)
        if report and report.get("status") == "ok":
            success += 1
        else:
            failed += 1

    click.echo(f"\n{'='*60}")
    click.echo(f"Batch complete: {success} succeeded, {failed} failed")
    click.echo(f"{'='*60}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    cli()
