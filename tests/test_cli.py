"""Tests for Click CLI interface."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from comicvid.cli import cli

pytestmark = pytest.mark.skipif(
    subprocess.run(["which", "ffmpeg"], capture_output=True).returncode != 0,
    reason="ffmpeg not installed",
)


@pytest.fixture
def panel_images(tmp_path: Path) -> Path:
    """Create test images using ffmpeg."""
    img_dir = tmp_path / "panels"
    img_dir.mkdir()
    for i, color in enumerate(["red", "green", "blue"]):
        out = img_dir / f"panel_{i:02d}.png"
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


class TestCliRender:
    def test_render_with_defaults(self, tmp_path: Path, panel_images: Path):
        """Basic render command."""
        output = tmp_path / "output.mp4"
        runner = CliRunner()
        result = runner.invoke(cli, [
            "render",
            str(panel_images),
            "-o", str(output),
            "--per-image-duration", "1",
            "--fps", "10",
            "--crf", "28",
            "--video-bitrate", "500k",
            "--keep-temps",
        ])
        assert result.exit_code == 0, result.output
        assert output.exists()
        assert output.stat().st_size > 1000

    def test_render_with_resolution_flag(self, tmp_path: Path, panel_images: Path):
        """Render with --resolution shortcut."""
        output = tmp_path / "res.mp4"
        runner = CliRunner()
        result = runner.invoke(cli, [
            "render",
            str(panel_images),
            "-o", str(output),
            "--resolution", "540x960",
            "--per-image-duration", "1",
            "--fps", "10",
            "--crf", "28",
            "--video-bitrate", "500k",
            "--keep-temps",
        ])
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_render_with_text_subtitles(self, tmp_path: Path, panel_images: Path):
        """Render with -t flags for per-image text."""
        output = tmp_path / "text_subs.mp4"
        runner = CliRunner()
        result = runner.invoke(cli, [
            "render",
            str(panel_images),
            "-o", str(output),
            "-t", "Hello",
            "-t", "World",
            "-t", "Test",
            "--per-image-duration", "1",
            "--fps", "10",
            "--crf", "28",
            "--video-bitrate", "500k",
            "--keep-temps",
        ])
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_render_invalid_resolution(self, tmp_path: Path, panel_images: Path):
        """Invalid --resolution should error."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "render",
            str(panel_images),
            "--resolution", "bad",
        ])
        assert result.exit_code != 0


class TestCliBatch:
    def test_batch_empty_dir(self, tmp_path: Path):
        """Batch with no subdirectories."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "batch", str(tmp_path),
        ])
        assert result.exit_code != 0
        assert "No subdirectories" in result.output

    def test_batch_with_subdirs(self, tmp_path: Path):
        """Batch with panel directories."""
        ep1 = tmp_path / "episode_01"
        ep1.mkdir()
        for i, color in enumerate(["red", "green"]):
            out = ep1 / f"panel_{i:02d}.png"
            subprocess.run(
                ["ffmpeg", "-y", "-f", "lavfi", "-i",
                 f"color=c={color}:s=640x480:d=0.1",
                 "-frames:v", "1", str(out)],
                capture_output=True, check=True,
            )

        output_dir = tmp_path / "out"
        runner = CliRunner()
        result = runner.invoke(cli, [
            "batch",
            str(tmp_path),
            "--output-dir", str(output_dir),
            "--per-image-duration", "1",
            "--keep-temps",
        ])
        assert result.exit_code == 0, result.output
        assert (output_dir / "episode_01.mp4").exists()


class TestCliVersion:
    def test_version_flag(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "comicvid" in result.output

    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "comicvid" in result.output
