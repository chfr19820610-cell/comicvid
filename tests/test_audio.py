"""Tests for audio module — reencode and duration probe."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from comicvid.audio import get_audio_duration, reencode_audio

# Skip all tests if ffmpeg not found
pytestmark = pytest.mark.skipif(
    subprocess.run(["which", "ffmpeg"], capture_output=True).returncode != 0,
    reason="ffmpeg not installed",
)


@pytest.fixture
def wav_file(tmp_path: Path) -> Path:
    """Generate a tiny valid WAV file using ffmpeg."""
    path = tmp_path / "test.wav"
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
            "-ac", "1", "-ar", "44100",
            str(path),
        ],
        capture_output=True,
        check=True,
    )
    return path


class TestReencodeAudio:
    def test_reencode_to_aac(self, tmp_path: Path, wav_file: Path):
        """Re-encode a WAV to AAC."""
        aac_path = tmp_path / "output.aac"
        result = reencode_audio(wav_file, aac_path)
        assert result is True
        assert aac_path.exists()
        assert aac_path.stat().st_size > 100

    def test_reencode_with_custom_params(self, tmp_path: Path, wav_file: Path):
        """Re-encode with non-default parameters."""
        aac_path = tmp_path / "custom.aac"
        result = reencode_audio(
            wav_file, aac_path,
            ffmpeg="ffmpeg",
            sample_rate=22050,
            bitrate="64k",
            channels=2,
        )
        assert result is True
        assert aac_path.exists()

    def test_reencode_fails_on_nonexistent_input(self, tmp_path: Path):
        """Should return False when input doesn't exist."""
        result = reencode_audio(
            tmp_path / "nonexistent.wav",
            tmp_path / "out.aac",
        )
        assert result is False

    def test_reencode_fails_on_directory_as_input(self, tmp_path: Path):
        """Should return False on invalid input."""
        result = reencode_audio(tmp_path, tmp_path / "out.aac")
        assert result is False


class TestGetAudioDuration:
    def test_returns_duration(self, wav_file: Path):
        """Should return ~2.0s for a 2-second sine tone."""
        duration = get_audio_duration(wav_file)
        assert 1.5 < duration < 3.0  # allow some tolerance

    def test_fallback_on_nonexistent_file(self, tmp_path: Path):
        """Should return 5.0 fallback for missing files."""
        duration = get_audio_duration(tmp_path / "missing.wav")
        assert duration == 5.0
