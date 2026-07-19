"""Audio utilities: re-encode to AAC, probe duration."""

from __future__ import annotations

import subprocess
from pathlib import Path


def reencode_audio(
    audio_path: Path,
    output_path: Path,
    ffmpeg: str = "ffmpeg",
    sample_rate: int = 44100,
    bitrate: str = "128k",
    channels: int = 1,
) -> bool:
    """Re-encode any audio to AAC at a consistent format.

    Args:
        audio_path: Input audio file path.
        output_path: Output AAC file path.
        ffmpeg: FFmpeg binary.
        sample_rate: Output sample rate in Hz.
        bitrate: Output bitrate (e.g. '128k').
        channels: Number of audio channels (1=mono).

    Returns:
        True on success.
    """
    cmd = [
        ffmpeg, "-y",
        "-i", str(audio_path),
        "-c:a", "aac",
        "-ar", str(sample_rate),
        "-b:a", bitrate,
        "-ac", str(channels),
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [audio] reencode failed: {result.stderr[-500:]}")
        return False
    return True


def get_audio_duration(audio_path: Path, ffmpeg: str = "ffmpeg") -> float:
    """Get audio duration in seconds using ffmpeg/ffprobe.

    Args:
        audio_path: Path to audio file.
        ffmpeg: FFmpeg binary path.

    Returns:
        Duration in seconds, or 5.0 on failure.
    """
    result = subprocess.run(
        [ffmpeg, "-i", str(audio_path), "-hide_banner"],
        capture_output=True, text=True,
    )
    for line in result.stderr.split("\n"):
        if "Duration" in line:
            parts = line.strip().split(",")[0]
            dur_str = parts.split("Duration:")[-1].strip()
            h, m, s = dur_str.split(":")
            try:
                return int(h) * 3600 + int(m) * 60 + float(s)
            except ValueError:
                pass
    return 5.0
