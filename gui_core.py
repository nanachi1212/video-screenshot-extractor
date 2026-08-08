from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile


def build_download_args(downloader: list[str], source: str, url: str) -> list[str]:
    return downloader + [
        "--newline", "--no-playlist", "-f", "bv*+ba/b", "--merge-output-format", "mp4",
        "-o", source, url,
    ]


def create_zip(folder: Path) -> Path:
    archive = folder.with_suffix(".zip")
    with ZipFile(archive, "w", ZIP_DEFLATED) as zip_file:
        for frame in sorted(folder.glob("frame_*.png")):
            zip_file.write(frame, frame.name)
    return archive


def parse_ffmpeg_progress(line: str, duration: float = 120) -> int | None:
    match = re.search(r"time=(\d+):(\d+):(\d+(?:\.\d+)?)", line)
    if not match:
        return None
    seconds = int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3))
    return min(99, max(0, round(seconds / max(duration, 1) * 100)))
