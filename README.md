# comicvid

**Static images to animated video — Ken Burns zoom + ASS subtitles + audio sync.**

Turn a folder of images into a polished MP4 video with a single command. Pure FFmpeg + Python — zero API costs.

## Features

- **Ken Burns zoom** — subtle 100% → 105% camera movement on each image
- **ASS subtitles** — styled (28px font, black stroke, bottom-center) with Chinese font support
- **Audio sync** — AAC 44100 Hz mono, automatically synchronized to video
- **Landscape & portrait** — 1280×720 or 1080×1920 (any resolution)
- **Batch mode** — process multiple subfolders at once
- **Pure CLI** — no GUI, no config files, no API keys

## Installation

```bash
pip install comicvid
```

Requires **Python 3.10+** and **FFmpeg** installed on your system.

## Usage

### Basic render

```bash
comicvid render ./panels/ --output episode.mp4 --duration 30
```

### With subtitles and audio

```bash
comicvid render ./panels/ \
    --output episode.mp4 \
    --duration 30 \
    --subtitle captions.srt \
    --audio narration.wav \
    --width 1280 --height 720
```

### Per-image text subtitles

```bash
comicvid render ./panels/ \
    --output episode.mp4 \
    -t "Hello, world!" \
    -t "Second panel" \
    -t "Third panel" \
    --audio music.wav
```

### Vertical video (TikTok/Reels)

```bash
comicvid render ./panels/ \
    --output vertical.mp4 \
    --duration 60 \
    --resolution 1080x1920
```

### Batch mode (episode directories)

```bash
comicvid batch ./episodes/ --output-dir ./output/
```

### All options

```
Usage: comicvid render [OPTIONS] IMAGE_DIR

  Render images from IMAGE_DIR into an MP4 video.

Options:
  -o, --output TEXT               Output MP4 path.  [default: output.mp4]
  --duration FLOAT                Total video duration in seconds.
  --per-image-duration FLOAT      Seconds per image.  [default: 3.0]
  --subtitle FILE                 External subtitle file (SRT or ASS).
  --subtitle-format [ass|srt]     Subtitle format.  [default: ass]
  -t, --text TEXT                 Subtitle text per image.
  --audio FILE                    Audio file (WAV, MP3, etc.).
  --width INTEGER                 Output video width.  [default: 1280]
  --height INTEGER                Output video height.  [default: 720]
  --resolution TEXT               Shortcut: '1920x1080'.
  --fps INTEGER                   Frames per second.  [default: 24]
  --crf INTEGER                   H.264 CRF quality.  [default: 23]
  --video-bitrate TEXT            Video bitrate.  [default: 1500k]
  --zoom FLOAT                    Ken Burns zoom amount.  [default: 0.05]
  --ffmpeg TEXT                   FFmpeg binary path.  [default: ffmpeg]
  --keep-temps                    Keep temporary files.
  --help                          Show this message and exit.
```

## Input format

`IMAGE_DIR` should contain panel images sorted by filename. Supported formats:
- PNG, JPG, JPEG, WEBP, BMP

Images are processed in alphabetical order.

## How it works

1. **Scene building** — each image is looped for its duration with a Ken Burns `zoompan` filter (100% → 105%)
2. **Audio encoding** — `ffmpeg` re-encodes audio to AAC at 44100 Hz mono
3. **Subtitles** — ASS format with styled Chinese-capable fonts, burned into video
4. **Concatenation** — FFmpeg concat demuxer assembles scenes
5. **Output** — Final MP4 with H.264 video + AAC audio

## License

Apache 2.0
