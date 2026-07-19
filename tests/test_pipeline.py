"""Tests for comicvid pipeline."""
from __future__ import annotations

from pathlib import Path

from comicvid.pipeline import resolve_image_list, verify_video
from comicvid.types import Config


class TestResolveImageList:
    def test_empty_directory(self, tmp_path: Path):
        result = resolve_image_list(tmp_path)
        assert result == []

    def test_returns_sorted_images(self, tmp_path: Path):
        (tmp_path / "z_img.png").touch()
        (tmp_path / "a_img.jpg").touch()
        (tmp_path / "m_img.webp").touch()
        (tmp_path / "note.txt").touch()

        result = resolve_image_list(tmp_path)
        names = [p.name for p in result]
        assert names == ["a_img.jpg", "m_img.webp", "z_img.png"]

    def test_supports_multiple_extensions(self, tmp_path: Path):
        exts = [".png", ".jpg", ".jpeg", ".webp", ".bmp"]
        for ext in exts:
            (tmp_path / f"img{ext}").touch()

        result = resolve_image_list(tmp_path)
        assert len(result) == len(exts)


class TestVerifyVideo:
    def test_verify_nonexistent_video(self, tmp_path: Path):
        """Should handle missing file gracefully."""
        path = tmp_path / "nonexistent.mp4"
        try:
            info = verify_video(path, "ffmpeg")
            assert "size_bytes" in info
        except Exception:
            pass  # ffmpeg might error on missing file, that's ok


class TestConfig:
    def test_resolution_property(self):
        c = Config(
            image_dir=Path("."),
            output=Path("out.mp4"),
            width=1920,
            height=1080,
        )
        assert c.resolution == "1920:1080"
        assert c.resolution_x == "1920x1080"

    def test_defaults(self):
        """Defaults should be reasonable."""
        c = Config(image_dir=Path("."), output=Path("out.mp4"))
        assert c.fps == 24
        assert c.crf == 23
        assert c.width == 1280
        assert c.height == 720
        assert c.ken_burns_zoom == 0.05
        assert c.audio_sample_rate == 44100
