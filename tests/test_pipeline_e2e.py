"""Tests for pipeline — end-to-end render and utility functions."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from comicvid.pipeline import (
    render_video,
    resolve_image_list,
    verify_video,
    write_report,
)
from comicvid.types import Config

pytestmark = pytest.mark.skipif(
    subprocess.run(["which", "ffmpeg"], capture_output=True).returncode != 0,
    reason="ffmpeg not installed",
)


@pytest.fixture
def panel_images(tmp_path: Path) -> Path:
    """Create test images using ffmpeg."""
    img_dir = tmp_path / "panels"
    img_dir.mkdir()
    for i in range(3):
        out = img_dir / f"panel_{i:02d}.png"
        # Generate a colored test pattern
        color = ["red", "green", "blue"][i]
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", f"color=c={color}:s=640x480:d=0.1",
                "-frames:v", "1",
                str(out),
            ],
            capture_output=True, check=True,
        )
    return img_dir


@pytest.fixture
def audio_file(tmp_path: Path) -> Path:
    """Create a short audio tone."""
    path = tmp_path / "narration.wav"
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
            "-ac", "1", "-ar", "44100",
            str(path),
        ],
        capture_output=True, check=True,
    )
    return path


class TestResolveImageList:
    def test_basic_resolve(self, panel_images: Path):
        images = resolve_image_list(panel_images)
        assert len(images) == 3
        assert all(p.suffix == ".png" for p in images)

    def test_non_image_files_ignored(self, tmp_path: Path):
        (tmp_path / "image.png").touch()
        (tmp_path / "notes.txt").touch()
        (tmp_path / "data.json").touch()
        images = resolve_image_list(tmp_path)
        assert len(images) == 1
        assert images[0].name == "image.png"


class TestRenderVideo:
    def test_render_basic(self, tmp_path: Path, panel_images: Path):
        """End-to-end render without audio or subtitles."""
        output = tmp_path / "output.mp4"
        config = Config(
            image_dir=panel_images,
            output=output,
            per_image_duration=1.0,
            fps=10,
            crf=28,
            video_bitrate="500k",
            keep_temps=True,
        )
        report = render_video(config)
        assert report is not None
        assert report["status"] == "ok"
        assert output.exists()
        assert output.stat().st_size > 1000

    def test_render_with_audio(self, tmp_path: Path, panel_images: Path, audio_file: Path):
        """Render with audio sync."""
        output = tmp_path / "with_audio.mp4"
        config = Config(
            image_dir=panel_images,
            output=output,
            per_image_duration=1.0,
            audio=audio_file,
            fps=10,
            crf=28,
            video_bitrate="500k",
            keep_temps=True,
        )
        report = render_video(config)
        assert report is not None
        assert report["status"] == "ok"
        assert output.exists()

    def test_render_with_subtitles(self, tmp_path: Path, panel_images: Path):
        """Render with per-image subtitles."""
        output = tmp_path / "with_subs.mp4"
        config = Config(
            image_dir=panel_images,
            output=output,
            per_image_duration=1.0,
            subtitles=["First panel", "Second panel", "Third panel"],
            fps=10,
            crf=28,
            video_bitrate="500k",
            keep_temps=True,
        )
        report = render_video(config)
        assert report is not None
        assert report["status"] == "ok"
        assert output.exists()

    def test_render_with_duration(self, tmp_path: Path, panel_images: Path):
        """Render with total duration."""
        output = tmp_path / "duration.mp4"
        config = Config(
            image_dir=panel_images,
            output=output,
            duration=6.0,
            fps=10,
            crf=28,
            video_bitrate="500k",
            keep_temps=True,
        )
        report = render_video(config)
        assert report is not None
        assert report["status"] == "ok"

    def test_render_empty_directory(self, tmp_path: Path):
        """Should return None for empty image directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        config = Config(image_dir=empty_dir, output=tmp_path / "out.mp4")
        report = render_video(config)
        assert report is None

    def test_render_vertical(self, tmp_path: Path, panel_images: Path):
        """Render vertical video."""
        output = tmp_path / "vertical.mp4"
        config = Config(
            image_dir=panel_images,
            output=output,
            per_image_duration=1.0,
            width=540,
            height=960,
            fps=10,
            crf=28,
            video_bitrate="500k",
            keep_temps=True,
        )
        report = render_video(config)
        assert report is not None
        assert report["status"] == "ok"


class TestVerifyVideo:
    def test_verify_real_video(self, tmp_path: Path, panel_images: Path):
        """Verify a real rendered video."""
        output = tmp_path / "verify.mp4"
        config = Config(
            image_dir=panel_images,
            output=output,
            per_image_duration=1.0,
            fps=10,
            crf=28,
            video_bitrate="500k",
        )
        render_video(config)

        info = verify_video(output)
        assert info["size_mb"] > 0
        assert "duration" in info
        assert "video" in info
        assert info["passes"] is True


class TestWriteReport:
    def test_write_report_json(self, tmp_path: Path):
        report = {"status": "ok", "duration": "00:00:05.00"}
        path = tmp_path / "report.json"
        write_report(report, path)
        assert path.exists()
        content = path.read_text()
        assert "ok" in content
        assert "00:00:05.00" in content
