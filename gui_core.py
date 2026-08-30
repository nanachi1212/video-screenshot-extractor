from pathlib import Path
import json
import os
import re
import shutil
import subprocess
from zipfile import ZIP_DEFLATED, ZipFile

SETTINGS_FILE = Path.home() / ".video_screenshot_gui.json"


def find_ytdlp(app_dir: Path | None = None) -> str | None:
    candidates = []
    if app_dir:
        candidates.append(app_dir / "yt-dlp.exe")
    if path := shutil.which("yt-dlp"):
        return path
    for root in (Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Python",
                 Path(os.environ.get("APPDATA", "")) / "Python"):
        candidates.extend(root.glob("Python*/Scripts/yt-dlp.exe"))
    return next((str(path) for path in candidates if path.is_file()), None)


def find_deno() -> str | None:
    if path := shutil.which("deno"):
        return path
    path = Path.home() / ".deno/bin/deno.exe"
    return str(path) if path.is_file() else None


def load_output_folder() -> str | None:
    try:
        value = json.loads(SETTINGS_FILE.read_text(encoding="utf-8")).get("output_folder")
    except (OSError, ValueError, AttributeError):
        return None
    return value if isinstance(value, str) and value else None


def save_output_folder(folder: str) -> None:
    SETTINGS_FILE.write_text(json.dumps({"output_folder": folder}, ensure_ascii=False), encoding="utf-8")


def clear_source_work_files(source: Path) -> None:
    for path in (source, source.with_name(source.name + ".part")):
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise RuntimeError("無法清除上一個來源影片，請確認 source.mp4 未被其他程式占用。") from exc


def sanitize_task_name(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    return name[:120] or "video"


def resolve_task_name(downloader: list[str], url: str, js_runtime: str | None, manual_name: str | None = None) -> str:
    if manual_name and manual_name.strip():
        return sanitize_task_name(manual_name)
    runtime = ["--js-runtimes", f"deno:{js_runtime}"] if js_runtime else []
    result = subprocess.run(downloader + runtime + ["--no-playlist", "--get-title", url], capture_output=True, text=True, check=True)
    return sanitize_task_name(result.stdout.strip().splitlines()[-1])


def build_download_args(downloader: list[str], source: str, url: str, js_runtime: str | None = None) -> list[str]:
    runtime = ["--js-runtimes", f"deno:{js_runtime}"] if js_runtime else []
    return downloader + runtime + [
        "--newline", "--no-playlist", "-f", "bv*+ba/b", "--merge-output-format", "mp4",
        "-o", source, url,
    ]


def create_zip(folder: Path, frame_prefix: str = "frame_") -> Path:
    archive = folder.with_suffix(".zip")
    with ZipFile(archive, "w", ZIP_DEFLATED) as zip_file:
        for frame in sorted(folder.glob(f"{frame_prefix}*.png")):
            zip_file.write(frame, frame.name)
    return archive


def parse_ffmpeg_progress(line: str, duration: float = 120) -> int | None:
    match = re.search(r"time=(\d+):(\d+):(\d+(?:\.\d+)?)", line)
    if not match:
        return None
    seconds = int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3))
    return min(99, max(0, round(seconds / max(duration, 1) * 100)))
