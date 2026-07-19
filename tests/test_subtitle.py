"""Tests for comicvid subtitle generation."""
from __future__ import annotations

from pathlib import Path

from comicvid.subtitle import (
    build_ass,
    build_srt,
    write_ass,
    write_srt,
)


class TestBuildSrt:
    def test_basic_srt(self):
        durations = [3.0, 2.5]
        subtitles = ["Hello world", "Second line"]
        result = build_srt(durations, subtitles)

        assert "1" in result
        assert "00:00:00,000 --> 00:00:03,000" in result
        assert "Hello world" in result
        assert "2" in result
        assert "00:00:03,000 --> 00:00:05,500" in result
        assert "Second line" in result

    def test_empty_subtitles(self):
        durations = [3.0, 2.0]
        subtitles = ["First", ""]
        result = build_srt(durations, subtitles)

        assert "First" in result
        assert "Second line" not in result  # only one subtitle entry
        assert result.count("-->") == 1

    def test_all_empty(self):
        result = build_srt([5.0, 5.0], ["", ""])
        assert result == ""

    def test_timestamp_format(self):
        durations = [3661.5]  # 1h 1m 1.5s
        subtitles = ["Long"]
        result = build_srt(durations, subtitles)

        assert "01:01:01,500" in result


class TestBuildAss:
    def test_basic_ass(self):
        durations = [3.0, 2.5]
        subtitles = ["你好", "World"]
        result = build_ass(durations, subtitles, 1280, 720)

        assert "[Script Info]" in result
        assert "PlayResX: 1280" in result
        assert "PlayResY: 720" in result
        assert "[V4+ Styles]" in result
        assert "[Events]" in result
        # Style line contains font size 28 after font name
        assert ",28," in result
        assert "你好" in result
        assert "World" in result
        assert "Dialogue:" in result

    def test_ass_margins(self):
        durations = [5.0]
        subtitles = ["Test"]
        result = build_ass(durations, subtitles, 1920, 1080)

        assert "PlayResX: 1920" in result
        assert "PlayResY: 1080" in result

    def test_ass_empty_subtitles_skipped(self):
        durations = [3.0, 3.0]
        subtitles = ["First", ""]
        result = build_ass(durations, subtitles)

        assert "First" in result
        # "Dialogue" should appear exactly once (only for non-empty subtitle)
        dialogue_lines = [l for l in result.split("\n") if l.startswith("Dialogue:")]
        assert len(dialogue_lines) == 1

    def test_ass_escapes_special_chars(self):
        durations = [3.0]
        subtitles = ["Text with {braces} and \\backslash"]
        result = build_ass(durations, subtitles)

        assert "\\{braces\\}" in result
        assert "\\\\backslash" in result


class TestWriteFunctions:
    def test_write_srt(self, tmp_path: Path):
        path = tmp_path / "test.srt"
        result = write_srt(path, [3.0], ["Hello"])
        assert result == path
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "Hello" in content

    def test_write_ass(self, tmp_path: Path):
        path = tmp_path / "test.ass"
        result = write_ass(path, [3.0], ["Hello"])
        assert result == path
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "Hello" in content
