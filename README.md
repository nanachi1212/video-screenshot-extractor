# Video Screenshot Extractor

Windows GUI for downloading public videos and extracting scene-change screenshots.

## Features

- Scene-change screenshot extraction with adjustable sensitivity
- Live download and extraction progress
- Intermediate screenshot count while processing
- Optional MP4 download with video and audio merged
- Optional MP3 extraction
- Automatic PNG ZIP archive

## Requirements

- Windows
- Python 3.12+ for source use
- `ffmpeg` and `ffprobe` on PATH
- `yt-dlp` installed for source use; the packaged EXE uses the user-installed `yt-dlp.exe`

## Run from source

```powershell
python app.py
```

## Release

The packaged executable is published in GitHub Releases.

Only download videos you are authorized to save. The application does not bypass login, membership, paywall, or DRM restrictions.
