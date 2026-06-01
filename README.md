# Video Cutter / Trimmer / Uploader

A Python GUI tool for batch video cutting, trimming, compression, and uploading via FFmpeg.

## Features

- **Cut** — Split videos into equal-length segments
- **Trim** — Extract clips from start, end, or custom position
- **Compress** — Limit output file size by re-encoding
- **Upload** — Send videos to a remote API endpoint
- **Batch processing** — Handle multiple videos at once

## Screenshot

```
┌──────────────────────────────────────────┐
│       Video Cutter / Trimmer / Uploader  │
├──────────────────────────────────────────┤
│  Video List   [+Add] [xRemove] [Clear]   │
├──────────────────────────────────────────┤
│  [ Cut ]  [ Trim ]  [ Upload ]           │
│                                          │
│  Cut: segment length | Trim: duration    │
│  Upload: Base URL | API Key | [Upload]   │
├──────────────────────────────────────────┤
│  Save to: [path] [Browse]                │
│  [ ] Enable Compression  [___] MB        │
│  [Start Processing] [Stop]               │
│  Progress bar · Status                   │
└──────────────────────────────────────────┘
```

## Requirements

- **Python 3.x**
- **FFmpeg** — place `ffmpeg.exe` / `ffprobe.exe` in the program folder, or install system-wide
- **requests** library (for upload tab) — `pip install requests`

## Quick Start

**Windows:** Double-click `run.bat` (auto-detects Python)

**Other OS:**
```bash
pip install requests
python3 video_cutter.py
```

## Configuration — `config.json`

Edit `config.json` to set defaults:

```json
{
  "python_path": "",
  "api_base_url": "https://your-server.com",
  "api_token": "your-api-key"
}
```

| Field | Description |
|-------|-------------|
| `python_path` | Custom Python executable path (optional, auto-detected) |
| `api_base_url` | Your upload API server URL |
| `api_token` | API key / Bearer token for authentication |

## Upload Tab

The **Upload** tab sends videos listed in the video list to a remote server:

1. Fill in **Base URL** (e.g. `https://your-server.com`)
2. Fill in **API Key** (sent as `Authorization: Bearer <key>`)
3. Click **Save Config** to persist to `config.json`
4. Add videos to the list (same list as Cut/Trim)
5. Click **Upload All Videos**

The default implementation sends a `POST` to `{base_url}/api/upload` with:
- `Content-Type: multipart/form-data`
- Field `file`: the video file
- Header `Authorization: Bearer {api_key}` (if key is set)

> **Important:** The upload feature is a **template** — you MUST customize it to match your target website's API. Every website has a different upload endpoint, authentication method, and response format. Edit the `_upload_seq` method in `video_cutter.py` to adapt:
> - **Endpoint URL** — change `/api/upload` to your server's upload path
> - **Headers** — adjust `Authorization` type (Bearer, API-Key, etc.) or add cookies
> - **Request body** — modify the multipart form fields or switch to JSON
> - **Response handling** — update the success check logic

## Cut Mode

1. Select videos
2. Set segment length (minutes / seconds)
3. Choose output directory
4. Optionally enable compression
5. Click **Start**

Example: 3min20s video, cut every 1min → `video_001.mp4` (1min), `video_002.mp4` (1min), `video_003.mp4` (1min), `video_004.mp4` (20s)

## Trim Mode

1. Set **Target Duration** (e.g. 30 seconds)
2. Choose region: **Start** / **End** / **Custom** (specify start time)
3. Click **Start**

## Compression

Check "Enable Compression" and set a target file size in MB. Videos smaller than the target are skipped. Uses libx264 with AAC audio.

## Project Structure

```
release/
├── video_cutter.py    # Main program
├── run.bat            # Windows launcher (auto-detects Python)
├── config.json        # User configuration (URL, token, etc.)
├── ffmpeg.exe         # FFmpeg (optional, auto-detected)
├── ffprobe.exe        # FFprobe (optional)
├── .gitignore
└── README.md
```

## How It Works

- **ffprobe** reads video duration, **ffmpeg** cuts/trims with `-c copy` (fast, lossless)
- Compression re-encodes with calculated bitrate based on target file size
- Upload uses `requests` multipart POST with Bearer authentication
- **run.bat** scans 6 common Python install locations automatically

## License

MIT
