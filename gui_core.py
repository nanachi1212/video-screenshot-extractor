from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

SETTINGS_FILE = Path.home() / ".video_screenshot_gui.json"
FRAME_PREFIX = "frame_"
FRAME_FILE_PATTERN = "frame_%04d.png"
FRAME_GLOB_PATTERN = "frame_*.png"


def get_subprocess_silent_flags() -> dict[str, object]:
    """Return subprocess flags to prevent popping up console/command prompt windows on Windows."""
    flags: dict[str, object] = {}
    if sys.platform == "win32":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        flags["creationflags"] = creationflags
        if hasattr(subprocess, "STARTUPINFO") and hasattr(subprocess, "STARTF_USESHOWWINDOW"):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE
            flags["startupinfo"] = startupinfo
    return flags


def run_silent(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Execute subprocess.run with windowless flags on Windows while preserving all capture options."""
    opts = get_subprocess_silent_flags()
    if "creationflags" in kwargs and "creationflags" in opts:
        kwargs["creationflags"] = kwargs["creationflags"] | opts["creationflags"]
    elif "creationflags" in opts:
        kwargs["creationflags"] = opts["creationflags"]
    if "startupinfo" in opts and "startupinfo" not in kwargs:
        kwargs["startupinfo"] = opts["startupinfo"]
    return subprocess.run(cmd, **kwargs)


def popen_silent(cmd: list[str], **kwargs) -> subprocess.Popen:
    """Execute subprocess.Popen with windowless flags on Windows while preserving pipes and stdout/stderr."""
    opts = get_subprocess_silent_flags()
    if "creationflags" in kwargs and "creationflags" in opts:
        kwargs["creationflags"] = kwargs["creationflags"] | opts["creationflags"]
    elif "creationflags" in opts:
        kwargs["creationflags"] = opts["creationflags"]
    if "startupinfo" in opts and "startupinfo" not in kwargs:
        kwargs["startupinfo"] = opts["startupinfo"]
    return subprocess.Popen(cmd, **kwargs)


def kill_process_tree(proc: subprocess.Popen | None) -> None:
    """Safely terminate a subprocess and any of its child processes to prevent zombies."""
    if proc is None:
        return
    try:
        if proc.poll() is not None:
            return
        if sys.platform == "win32":
            run_silent(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        else:
            proc.kill()
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def resolve_tool(tool_name: str, app_dir: Path | None = None) -> str | None:
    """
    Resolve absolute path to an external tool binary.
    Priority:
      1. <app_dir>/tools/<tool_name>[.exe] (Bundled tools have top priority)
      2. <app_dir>/<tool_name>[.exe]
      3. System PATH
      4. Known installation paths (yt-dlp Python Scripts, Deno user profile)
    """
    base_name = tool_name.removesuffix(".exe")
    exe_name = f"{base_name}.exe" if sys.platform == "win32" or not base_name.endswith(".exe") else base_name

    # 1. Bundled tools folder (Highest priority)
    if app_dir:
        bundled_in_tools = app_dir / "tools" / exe_name
        if bundled_in_tools.is_file():
            return str(bundled_in_tools.resolve())
        bundled_in_app = app_dir / exe_name
        if bundled_in_app.is_file():
            return str(bundled_in_app.resolve())

    # 2. System PATH
    if path := shutil.which(base_name) or shutil.which(exe_name):
        return str(Path(path).resolve())

    # 3. Known fallback locations
    if base_name == "yt-dlp":
        for root in (
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Python",
            Path(os.environ.get("APPDATA", "")) / "Python",
        ):
            if root.exists():
                candidates = list(root.glob("Python*/Scripts/yt-dlp.exe"))
                for candidate in candidates:
                    if candidate.is_file():
                        return str(candidate.resolve())

    elif base_name == "deno":
        user_deno = Path.home() / ".deno" / "bin" / exe_name
        if user_deno.is_file():
            return str(user_deno.resolve())

    return None


def find_ytdlp(app_dir: Path | None = None) -> str | None:
    """Find yt-dlp executable, checking bundled location first, then PATH and Python user scripts."""
    return resolve_tool("yt-dlp", app_dir)


def find_deno(app_dir: Path | None = None) -> str | None:
    """Find deno executable, checking bundled location first, then PATH and user profile."""
    return resolve_tool("deno", app_dir)


def find_ffmpeg(app_dir: Path | None = None) -> str | None:
    """Find ffmpeg executable, checking bundled location first, then PATH."""
    return resolve_tool("ffmpeg", app_dir)


def find_ffprobe(app_dir: Path | None = None) -> str | None:
    """Find ffprobe executable, checking bundled location first, then PATH."""
    return resolve_tool("ffprobe", app_dir)


def check_runtime_tools(app_dir: Path | None = None) -> dict[str, str | None]:
    """
    Check all required and optional external tools at once.
    Returns a dictionary mapping tool name to resolved path or None.
    """
    return {
        "ffmpeg": find_ffmpeg(app_dir),
        "ffprobe": find_ffprobe(app_dir),
        "yt-dlp": find_ytdlp(app_dir),
        "deno": find_deno(app_dir),
    }


def load_output_folder() -> str | None:
    try:
        value = json.loads(SETTINGS_FILE.read_text(encoding="utf-8")).get("output_folder")
    except (OSError, ValueError, AttributeError):
        return None
    return value if isinstance(value, str) and value else None


def save_output_folder(folder: str) -> None:
    try:
        SETTINGS_FILE.write_text(json.dumps({"output_folder": folder}, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def clear_source_work_files(source: Path) -> None:
    """Clear intermediate source files."""
    for path in (source, source.with_name(source.name + ".part")):
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise RuntimeError("無法清除上一個來源影片，請確認 source.mp4 未被其他程式占用。") from exc


def sanitize_task_name(name: str) -> str:
    """Sanitize title or manual name to be safe for filenames across Windows filesystems."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    return name[:120] or "video"


def extract_video_id(url: str) -> str | None:
    """Extract a stable video/post identifier from supported URL shapes when available."""
    patterns = [
        r"(?:v=|\/v\/|youtu\.be\/|embed\/|shorts\/|live\/)([A-Za-z0-9_-]{11})",
        r"[?&]v=([A-Za-z0-9_-]+)",
        r"threads\.(?:com|net)\/(?:@[^/?#]+\/post|t)\/([A-Za-z0-9_-]+)",
        r"threads\.(?:com|net)\/share\/([A-Za-z0-9_-]+)",
    ]
    for p in patterns:
        if m := re.search(p, url):
            return m.group(1)
    return None


def get_safe_output_dir(base_output: Path, title: str, video_id: str | None = None) -> Path:
    """
    Determine a non-destructive output folder path.
    Format:
        <title> [<video_id>]  (or <title> if no video_id)
    If target directory or file already exists, appends ' (2)', ' (3)', etc.
    Guarantees that existing user outputs are NEVER overwritten or deleted.
    """
    clean_title = sanitize_task_name(title)
    if video_id and video_id.strip():
        clean_id = sanitize_task_name(video_id.strip())
        folder_name = f"{clean_title} [{clean_id}]"
    else:
        folder_name = clean_title

    candidate = base_output / folder_name
    if not candidate.exists():
        return candidate

    counter = 2
    while True:
        candidate = base_output / f"{folder_name} ({counter})"
        if not candidate.exists():
            return candidate
        counter += 1



def resolve_ytdlp_plugin_dir(app_dir: Path) -> str | None:
    """Return the directory yt-dlp must search for the bundled plugin namespace."""
    if (app_dir / "plugins" / "yt_dlp_plugins").is_dir():
        return str(app_dir)
    return None


def build_ytdlp_common_args(js_runtime: str | None = None, plugin_dir: str | None = None) -> list[str]:
    """Build shared yt-dlp options for bundled runtime and extractor plugins."""
    args: list[str] = []
    if plugin_dir:
        args.extend(["--plugin-dirs", plugin_dir])
    if js_runtime:
        args.extend(["--js-runtimes", f"deno:{js_runtime}"])
    return args


def resolve_task_name(
    downloader: list[str],
    url: str,
    js_runtime: str | None,
    manual_name: str | None = None,
    plugin_dir: str | None = None,
) -> str:
    """Retrieve video title or return sanitized manual name."""
    if manual_name and manual_name.strip():
        return sanitize_task_name(manual_name)
    common = build_ytdlp_common_args(js_runtime, plugin_dir)
    result = run_silent(
        downloader + common + ["--no-playlist", "--get-title", url],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(detail or f"無法取得影片資訊，yt-dlp 返回碼：{result.returncode}")
    lines = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
    return sanitize_task_name(lines[-1] if lines else "video")


def build_download_args(
    downloader: list[str],
    source: str,
    url: str,
    js_runtime: str | None = None,
    plugin_dir: str | None = None,
) -> list[str]:
    """Construct yt-dlp arguments for downloading video with best video + best audio merged into mp4."""
    common = build_ytdlp_common_args(js_runtime, plugin_dir)
    return downloader + common + [
        "--newline",
        "--no-playlist",
        "-f",
        "bv*+ba/b",
        "--merge-output-format",
        "mp4",
        "-o",
        source,
        url,
    ]


def count_frames(folder: Path, pattern: str = FRAME_GLOB_PATTERN) -> int:
    """Count image frames currently in directory."""
    if not folder.is_dir():
        return 0
    return len(list(folder.glob(pattern)))


def create_zip(folder: Path, frame_prefix: str = FRAME_PREFIX, target_zip: Path | None = None) -> Path:
    """
    Create a zip archive containing only the frame images.
    If target_zip is given, write to it, otherwise default to folder.with_suffix('.zip').
    """
    archive = target_zip or folder.with_suffix(".zip")
    with ZipFile(archive, "w", ZIP_DEFLATED) as zip_file:
        for frame in sorted(folder.glob(f"{frame_prefix}*.png")):
            zip_file.write(frame, frame.name)
    return archive


def parse_ffmpeg_progress(line: str, duration: float = 120) -> int | None:
    """Parse time from ffmpeg progress stdout line and return percentage (0-99)."""
    match = re.search(r"time=(\d+):(\d+):(\d+(?:\.\d+)?)", line)
    if not match:
        return None
    seconds = int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3))
    return min(99, max(0, round(seconds / max(duration, 1) * 100)))


def create_job_workspace() -> Path:
    """Create an isolated, dedicated temporary job directory in system temp folder."""
    base_temp = Path(tempfile.gettempdir()) / "VideoScreenshotExtractor"
    base_temp.mkdir(parents=True, exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix="job_", dir=base_temp))
    (workspace / "frames").mkdir(parents=True, exist_ok=True)
    return workspace


def cleanup_job_workspace(workspace: Path | None) -> None:
    """Safely and recursively remove a job workspace directory."""
    if workspace is None:
        return
    try:
        if workspace.exists():
            shutil.rmtree(workspace, ignore_errors=True)
    except Exception:
        pass


def classify_error(exc: Exception | str) -> str:
    """
    Translate technical errors from yt-dlp, FFmpeg, or OS into user-friendly Chinese messages
    while retaining context.
    """
    msg = str(exc).lower()
    if "403" in msg or "forbidden" in msg:
        return "存取被拒 (403 Forbidden)。影片下載權限受限或 URL 憑據過期，請確認影片權限或更新工具。"
    if "post" in msg and ("private" in msg or "login-gated" in msg):
        return "無法存取這則 Threads 貼文：貼文可能是私人內容、需要登入，或已被移除。"
    if "private video" in msg or "sign in" in msg or "members-only" in msg or "login" in msg:
        return "無法存取該影片：此影片為私人影片、會員專屬或需要登入方可觀看。"
    if "no downloadable video" in msg or "contains no videos" in msg:
        return "這則 Threads 貼文沒有可下載的影片，可能是純圖片、純文字或目前不支援的貼文類型。"
    if "video unavailable" in msg or "not found" in msg or "404" in msg:
        return "影片不存在或已被移除。"
    if "js-runtimes" in msg or "deno" in msg or "challenge" in msg or "bot" in msg:
        return "YouTube 機器人驗證或 JavaScript challenge 失敗。請確認隨附或已安裝 Deno。"
    if "no space left" in msg or "disk full" in msg:
        return "硬碟儲存空間不足，請釋放磁碟空間後重試。"
    if "permission denied" in msg or "access is denied" in msg:
        return "檔案或資料夾存取被拒。請確認輸出資料夾有寫入權限，且檔案未被其他程式鎖定。"
    if "connection" in msg or "network" in msg or "timeout" in msg or "timed out" in msg:
        return "網路連線失敗或逾時，請檢查網路連線後重試。"
    if "ffmpeg" in msg or "ffprobe" in msg:
        return "FFmpeg 影片處理或畫面分析失敗，可能影片編碼異常或檔案損毀。"
    return f"處理發生錯誤：{exc}"


def format_summary(elapsed_seconds: float, frame_count: int, has_mp4: bool, has_mp3: bool, has_zip: bool) -> str:
    """Format job completion summary text."""
    minutes = int(elapsed_seconds // 60)
    seconds = int(elapsed_seconds % 60)
    time_str = f"{minutes} 分 {seconds} 秒" if minutes > 0 else f"{seconds} 秒"

    lines = [
        "處理完成！",
        f"• 擷取圖片：{frame_count} 張" if frame_count > 0 else "• 擷取圖片：未選擇",
        f"• MP4 影片：{'已儲存' if has_mp4 else '未選擇'}",
        f"• MP3 音訊：{'已儲存' if has_mp3 else '未選擇'}",
        f"• 圖片 ZIP：{'已建立' if has_zip else '未選擇'}",
        f"• 總耗時：{time_str}",
    ]
    return "\n".join(lines)

