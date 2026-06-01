# Video Cutter / Trimmer / Uploader

Built with assistance from **CodeBuddy**, **DeepSeek**, 熊仔, and 乐平.

---

A blazing-fast video processing tool powered by FFmpeg. Cut, trim, compress, and upload videos — all in one lightweight GUI.

## Why This Tool?

Most free video editors re-encode every frame, taking minutes or hours. This tool uses **ffmpeg -c copy** for cutting and trimming — zero re-encoding, nearly instant results. Compression is the only step that re-encodes, and even that is optimized with calculated bitrate targeting.

| Operation | Speed | Method |
|-----------|-------|--------|
| Cut / Trim | **Instant** | `-c copy` (lossless stream copy) |
| Compress | Fast | libx264 + AAC, bitrate-targeted |
| Upload | Network-bound | multipart POST with Bearer auth |

## Features

- **Cut** — Split videos into equal-length segments without re-encoding
- **Trim** — Extract clips from start, end, or custom timestamp range
- **Compress** — Re-encode to a target file size with calculated bitrate
- **Upload** — Send processed videos to any REST API endpoint
- **Batch Processing** — Select multiple videos, process them all at once
- **Stop Anytime** — Cancel mid-operation; completed files are kept

## Upload API Customization

> **Note:** The upload feature provides a template implementation (`_upload_seq` method in `video_cutter.py`). You **must customize** it for your target server:
> - Change `POST /api/upload` to your actual endpoint
> - Adjust authentication (Bearer, API-Key, Cookie, etc.)
> - Modify request body format (multipart, JSON, etc.)
> - Update response handling for your API

## Requirements

- **Python 3.x**
- **FFmpeg** — install system-wide, or place `ffmpeg.exe` / `ffprobe.exe` in the program folder
- **requests** — `pip install requests` (required for upload tab only)

## Quick Start

**Windows:** Double-click `run.bat` (auto-detects Python from 6 common install locations)

**macOS / Linux:**
```bash
pip install requests
python3 video_cutter.py
```

## Configuration

Copy `config.json` template and fill in your settings:

```json
{
  "python_path": "",
  "api_base_url": "https://your-server.com",
  "api_token": "your-api-key"
}
```

## Project Structure

```
├── video_cutter.py    # Main program
├── run.bat            # Windows launcher
├── config.json        # User configuration (gitignored)
├── .gitignore
└── README.md
```

## License

MIT