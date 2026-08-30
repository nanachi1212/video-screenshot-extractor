# Video Screenshot Extractor

Windows GUI for downloading public videos and extracting scene-change screenshots.

## Features

- Scene-change screenshot extraction with adjustable sensitivity
- Live download and extraction progress
- Intermediate screenshot count while processing
- Optional MP4 download with video and audio merged
- Optional MP3 extraction
- Automatic PNG ZIP archive
- Automatic naming from the video title, or a user-provided task name for MP4, MP3, screenshots, and ZIP output

## Requirements

- Windows
- Python 3.12+ for source use
- `ffmpeg` and `ffprobe` on PATH
- `yt-dlp` installed; the app searches for `yt-dlp.exe` automatically
- Deno installed; it supports yt-dlp's JavaScript challenge handling for current YouTube downloads

The app automatically detects Deno from PATH or `%USERPROFILE%\\.deno\\bin\\deno.exe`; no full path entry is required.

## Run from source

```powershell
python app.py
```

## Release

The packaged executable is published in GitHub Releases.

Only download videos you are authorized to save. The application does not bypass login, membership, paywall, or DRM restrictions.
