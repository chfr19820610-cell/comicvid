"""SRT and ASS subtitle generation.

SRT: Simple, widely compatible plain-text format.
ASS: Advanced SubStation Alpha — styled (font size, stroke, position).
"""

from __future__ import annotations

from pathlib import Path


def _srt_ts(sec: float) -> str:
    """Format seconds as SRT timestamp: HH:MM:SS,mmm"""
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int((sec - int(sec)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _ass_ts(sec: float) -> str:
    """Format seconds as ASS timestamp: H:MM:SS.mm"""
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def build_srt(
    durations: list[float],
    subtitles: list[str],
) -> str:
    """Build SRT subtitle content.

    Args:
        durations: Duration in seconds for each segment.
        subtitles: Subtitle text per segment (empty string = no subtitle).

    Returns:
        Complete SRT file content.
    """
    lines: list[str] = []
    current_time = 0.0
    sub_idx = 0

    for dur, text in zip(durations, subtitles):
        if not text:
            current_time += dur
            continue
        sub_idx += 1
        lines.append(str(sub_idx))
        lines.append(f"{_srt_ts(current_time)} --> {_srt_ts(current_time + dur)}")
        lines.append(text)
        lines.append("")
        current_time += dur

    return "\n".join(lines)


def build_ass(
    durations: list[float],
    subtitles: list[str],
    video_width: int = 1280,
    video_height: int = 720,
    font_size: int = 28,
    border_size: int = 2,
) -> str:
    """Build ASS subtitle content with styled formatting.

    ASS provides:
    - Font size (28px for readability)
    - Border/outline (2px black stroke)
    - Position (bottom-center)
    - Shadow and colors

    Args:
        durations: Duration in seconds for each segment.
        subtitles: Subtitle text per segment.
        video_width, video_height: Output video dimensions.
        font_size: Subtitle font size.
        border_size: Black outline thickness.

    Returns:
        Complete ASS file content.
    """
    margin_v = int(video_height * 0.05)
    margin_h = int(video_width * 0.02)

    lines: list[str] = []
    lines.append("[Script Info]")
    lines.append("Title: comicvid Subtitles")
    lines.append("ScriptType: v4.00+")
    lines.append(f"PlayResX: {video_width}")
    lines.append(f"PlayResY: {video_height}")
    lines.append("ScaledBorderAndShadow: yes")
    lines.append("")

    lines.append("[V4+ Styles]")
    lines.append(
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding"
    )
    primary = "&H00FFFFFF"
    outline = "&H00000000"
    font_name = _resolve_font_name()
    lines.append(
        f"Style: Default,{font_name},{font_size},"
        f"{primary},{primary},"
        f"{outline},{outline},"
        f"0,0,0,0,"
        f"100,100,0,0,"
        f"1,{border_size},0,"
        f"2,"
        f"{margin_h},{margin_h},{margin_v},"
        f"1"
    )
    lines.append("")

    lines.append("[Events]")
    lines.append(
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, "
        "MarginV, Effect, Text"
    )

    current_time = 0.0
    for dur, text in zip(durations, subtitles):
        if not text:
            current_time += dur
            continue
        escaped = text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
        lines.append(
            f"Dialogue: 0,{_ass_ts(current_time)},{_ass_ts(current_time + dur)},"
            f"Default,,0,0,0,,{escaped}"
        )
        current_time += dur

    return "\n".join(lines)


def write_srt(path: Path, durations: list[float], subtitles: list[str]) -> Path:
    """Write SRT file and return path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = build_srt(durations, subtitles)
    path.write_text(content, encoding="utf-8")
    return path


def write_ass(
    path: Path,
    durations: list[float],
    subtitles: list[str],
    video_width: int = 1280,
    video_height: int = 720,
) -> Path:
    """Write ASS file and return path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = build_ass(durations, subtitles, video_width, video_height)
    path.write_text(content, encoding="utf-8")
    return path


def _resolve_font_name() -> str:
    """Resolve a readable Chinese-capable font name for ASS.

    Tries common system fonts; falls back to sans-serif.
    """
    import subprocess
    import sys

    candidates = [
        "PingFang SC",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "STHeiti",
        "Arial Unicode MS",
    ]

    for name in candidates:
        try:
            result = subprocess.run(
                ["fc-list", f":lang=zh"],
                capture_output=True, text=True, timeout=3,
            )
            if name.lower() in result.stdout.lower():
                return name
        except Exception:
            pass

    # Try common system fonts without Chinese filtering
    for name in candidates:
        try:
            result = subprocess.run(
                ["fc-list", name],
                capture_output=True, text=True, timeout=3,
            )
            if name.lower() in result.stdout.lower():
                return name
        except Exception:
            pass

    return "sans-serif"
