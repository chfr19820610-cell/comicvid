"""Configuration dataclass for comicvid rendering."""

from __future__ import annotations

import dataclasses
from pathlib import Path


@dataclasses.dataclass
class Config:
    """Render configuration for a single comicvid video."""

    # Input paths
    image_dir: Path
    """Directory containing panel images (sorted by filename)."""

    # Output
    output: Path
    """Output MP4 path."""

    # Timing
    duration: float | None = None
    """Total video duration in seconds. If None, infer from image count."""

    per_image_duration: float = 3.0
    """Seconds per image when duration is not specified."""

    # Subtitles
    subtitle: Path | None = None
    """Optional external subtitle file (SRT or ASS)."""

    subtitle_format: str = "ass"
    """Subtitle format: 'ass' (styled) or 'srt' (simple)."""

    subtitles: list[str] | None = None
    """Optional list of subtitle texts, one per image. Generated as ASS."""

    # Audio
    audio: Path | None = None
    """Optional audio file (WAV, MP3, etc.). AAC-encoded before muxing."""

    # Resolution
    width: int = 1280
    """Output video width in pixels."""

    height: int = 720
    """Output video height in pixels."""

    # Video quality
    fps: int = 24
    """Frames per second."""

    crf: int = 23
    """H.264 CRF quality (lower = better, 18-28 typical)."""

    video_bitrate: str = "1500k"
    """Video bitrate."""

    # Audio quality
    audio_sample_rate: int = 44100
    """Audio sample rate in Hz."""

    audio_bitrate: str = "128k"
    """Audio bitrate."""

    # Ken Burns
    ken_burns_zoom: float = 0.05
    """Zoom amount (0.05 = 100% → 105%)."""

    # Rendering
    ffmpeg: str = "ffmpeg"
    """FFmpeg binary path."""

    temp_dir: Path = Path("/tmp") / "comicvid"
    """Temporary working directory."""

    keep_temps: bool = False
    """If True, do not clean up temporary files."""

    @property
    def resolution(self) -> str:
        return f"{self.width}:{self.height}"

    @property
    def resolution_x(self) -> str:
        return f"{self.width}x{self.height}"
