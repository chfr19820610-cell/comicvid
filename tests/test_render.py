"""Tests for comicvid render module."""
from __future__ import annotations

from pathlib import Path

from comicvid.render import build_scene_video
from comicvid.types import Config


class TestBuildSceneVideo:
    def test_returns_false_on_nonexistent_image(self, tmp_path: Path):
        """Should fail gracefully when image doesn't exist."""
        config = Config(
            image_dir=tmp_path,
            output=tmp_path / "out.mp4",
        )
        clip = tmp_path / "clip.mp4"
        img = tmp_path / "nonexistent.png"
        result = build_scene_video(clip, img, None, 3.0, config)
        assert result is False

    def test_returns_false_on_nonexistent_audio(self, tmp_path: Path):
        """Should fail gracefully when audio doesn't exist."""
        config = Config(
            image_dir=tmp_path,
            output=tmp_path / "out.mp4",
        )
        clip = tmp_path / "clip.mp4"
        img = tmp_path / "test.png"
        img.touch()  # exists but not a real image
        audio = tmp_path / "nonexistent.wav"
        result = build_scene_video(clip, img, audio, 3.0, config)
        assert result is False
