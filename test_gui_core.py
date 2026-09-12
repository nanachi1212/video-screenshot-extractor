import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import gui_core
from gui_core import (
    build_download_args,
    check_runtime_tools,
    classify_error,
    cleanup_job_workspace,
    clear_source_work_files,
    count_frames,
    create_job_workspace,
    create_zip,
    find_deno,
    find_ffmpeg,
    find_ffprobe,
    find_ytdlp,
    format_summary,
    get_subprocess_silent_flags,
    kill_process_tree,
    load_output_folder,
    parse_ffmpeg_progress,
    resolve_task_name,
    resolve_tool,
    sanitize_task_name,
    save_output_folder,
)


class GuiCoreTests(unittest.TestCase):
    def test_download_command_requests_video_and_audio(self):
        args = build_download_args(["yt-dlp"], "source.mp4", "https://example.com/video")
        self.assertIn("bv*+ba/b", args)
        self.assertIn("--merge-output-format", args)

    def test_download_command_adds_deno_when_available(self):
        args = build_download_args(["yt-dlp"], "source.mp4", "url", r"C:\deno.exe")
        self.assertEqual(args[1:3], ["--js-runtimes", r"deno:C:\deno.exe"])

    def test_download_command_works_without_deno(self):
        args = build_download_args(["yt-dlp"], "source.mp4", "url")
        self.assertNotIn("--js-runtimes", args)

    def test_clear_source_work_files_removes_source_and_part_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "source.mp4"
            source.write_bytes(b"old")
            source.with_name("source.mp4.part").write_bytes(b"partial")
            other = folder / "other.mp4"
            other.write_bytes(b"keep")
            clear_source_work_files(source)
            self.assertFalse(source.exists())
            self.assertFalse(source.with_name("source.mp4.part").exists())
            self.assertTrue(other.exists())

    def test_clear_source_work_files_allows_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            clear_source_work_files(Path(tmp) / "source.mp4")

    def test_clear_source_work_files_reports_locked_source(self):
        source = Path("source.mp4")
        with patch.object(Path, "unlink", side_effect=OSError("locked")):
            with self.assertRaisesRegex(RuntimeError, "無法清除上一個來源影片"):
                clear_source_work_files(source)

    def test_manual_task_name_is_sanitized_without_downloader_call(self):
        self.assertEqual(resolve_task_name(["unused"], "url", None, "my:video"), "my_video")

    def test_auto_task_name_uses_title(self):
        result = type("Result", (), {"stdout": "A\nTitle\n", "stderr": ""})()
        with patch("gui_core.run_silent", return_value=result) as run:
            self.assertEqual(resolve_task_name(["yt-dlp"], "url", r"C:\deno.exe"), "Title")
            run.assert_called_once()

    def test_sanitize_task_name_removes_illegal_characters(self):
        self.assertEqual(sanitize_task_name('foo:bar*baz?test"one<two>three|four'), "foo_bar_baz_test_one_two_three_four")
        self.assertEqual(sanitize_task_name("   .name.  "), "name")
        self.assertEqual(sanitize_task_name(""), "video")

    # --- Tool Resolver & Priority Tests ---

    def test_resolve_tool_bundled_in_tools_has_top_priority(self):
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp)
            bundled_tools = app_dir / "tools"
            bundled_tools.mkdir(parents=True)
            bundled_bin = bundled_tools / "ffmpeg.exe"
            bundled_bin.write_text("fake binary")

            with patch("shutil.which", return_value=r"C:\Windows\System32\ffmpeg.exe"):
                resolved = resolve_tool("ffmpeg", app_dir=app_dir)
                self.assertEqual(resolved, str(bundled_bin.resolve()))

    def test_resolve_tool_bundled_in_app_dir_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp)
            bundled_bin = app_dir / "ffmpeg.exe"
            bundled_bin.write_text("fake binary")

            with patch("shutil.which", return_value=r"C:\Windows\System32\ffmpeg.exe"):
                resolved = resolve_tool("ffmpeg", app_dir=app_dir)
                self.assertEqual(resolved, str(bundled_bin.resolve()))

    def test_resolve_tool_falls_back_to_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp)  # Empty app_dir, no bundled tools
            with patch("shutil.which", return_value=r"C:\tools\ffmpeg.exe"):
                resolved = resolve_tool("ffmpeg", app_dir=app_dir)
                self.assertEqual(resolved, str(Path(r"C:\tools\ffmpeg.exe").resolve()))

    def test_resolve_tool_missing_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            app_dir = Path(tmp)
            with patch("shutil.which", return_value=None), patch.dict("os.environ", {"LOCALAPPDATA": "", "APPDATA": ""}):
                self.assertIsNone(resolve_tool("ffmpeg", app_dir=app_dir))
                self.assertIsNone(resolve_tool("nonexistent", app_dir=app_dir))

    def test_check_runtime_tools_returns_all_keys(self):
        with patch("gui_core.resolve_tool") as mock_resolve:
            mock_resolve.side_effect = lambda name, app_dir=None: f"/resolved/{name}"
            tools = check_runtime_tools()
            self.assertEqual(tools["ffmpeg"], "/resolved/ffmpeg")
            self.assertEqual(tools["ffprobe"], "/resolved/ffprobe")
            self.assertEqual(tools["yt-dlp"], "/resolved/yt-dlp")
            self.assertEqual(tools["deno"], "/resolved/deno")

    def test_find_ytdlp_from_path(self):
        with patch("shutil.which", return_value=r"C:\tools\yt-dlp.exe"):
            self.assertEqual(find_ytdlp(), str(Path(r"C:\tools\yt-dlp.exe").resolve()))

    def test_find_ytdlp_from_localappdata(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Programs/Python/Python313/Scripts/yt-dlp.exe"
            path.parent.mkdir(parents=True)
            path.touch()
            with patch.dict("os.environ", {"LOCALAPPDATA": tmp, "APPDATA": ""}, clear=False), patch("shutil.which", return_value=None):
                self.assertEqual(find_ytdlp(), str(path.resolve()))

    def test_find_ytdlp_from_appdata(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Python/Python313/Scripts/yt-dlp.exe"
            path.parent.mkdir(parents=True)
            path.touch()
            with patch.dict("os.environ", {"LOCALAPPDATA": "", "APPDATA": tmp}, clear=False), patch("shutil.which", return_value=None):
                self.assertEqual(find_ytdlp(), str(path.resolve()))

    def test_find_ytdlp_missing(self):
        with patch("shutil.which", return_value=None), patch.dict("os.environ", {"LOCALAPPDATA": "", "APPDATA": ""}, clear=False):
            self.assertIsNone(find_ytdlp())

    def test_find_deno_from_path(self):
        with patch("shutil.which", return_value=r"C:\deno.exe"):
            self.assertEqual(find_deno(), str(Path(r"C:\deno.exe").resolve()))

    def test_find_deno_from_user_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".deno/bin/deno.exe"
            path.parent.mkdir(parents=True)
            path.touch()
            with patch("shutil.which", return_value=None), patch("pathlib.Path.home", return_value=Path(tmp)):
                self.assertEqual(find_deno(), str(path.resolve()))

    def test_find_deno_missing(self):
        with patch("shutil.which", return_value=None), patch("pathlib.Path.home", return_value=Path(tempfile.mkdtemp())):
            self.assertIsNone(find_deno())

    # --- Windows Silent Process Flags ---

    def test_silent_subprocess_flags(self):
        flags = get_subprocess_silent_flags()
        if sys.platform == "win32":
            self.assertIn("creationflags", flags)
            self.assertEqual(flags["creationflags"] & subprocess.CREATE_NO_WINDOW, subprocess.CREATE_NO_WINDOW)
            self.assertIn("startupinfo", flags)
            si = flags["startupinfo"]
            self.assertTrue(si.dwFlags & subprocess.STARTF_USESHOWWINDOW)
            self.assertEqual(si.wShowWindow, 0)
        else:
            self.assertEqual(flags, {})

    # --- Job Workspace Isolation & Frame Counting ---

    def test_create_and_cleanup_job_workspace(self):
        ws = create_job_workspace()
        self.assertTrue(ws.is_dir())
        self.assertTrue((ws / "frames").is_dir())
        cleanup_job_workspace(ws)
        self.assertFalse(ws.exists())

    def test_cleanup_job_workspace_none_safe(self):
        cleanup_job_workspace(None)

    def test_count_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            self.assertEqual(count_frames(folder), 0)
            (folder / "frame_0001.png").touch()
            (folder / "frame_0002.png").touch()
            (folder / "other.txt").touch()
            self.assertEqual(count_frames(folder), 2)

    def test_old_images_do_not_pollute_new_job_zip(self):
        """Verify that a second job never contains remnants of a previous run."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Job 1: 15 frames
            ws1 = root / "ws1"
            ws1_frames = ws1 / "frames"
            ws1_frames.mkdir(parents=True)
            for i in range(1, 16):
                (ws1_frames / f"frame_{i:04d}.png").write_bytes(f"job1_frame{i}".encode())
            zip1 = create_zip(ws1_frames, target_zip=ws1 / "test_screenshots.zip")
            self.assertEqual(count_frames(ws1_frames), 15)

            # Job 2: 5 frames
            ws2 = root / "ws2"
            ws2_frames = ws2 / "frames"
            ws2_frames.mkdir(parents=True)
            for i in range(1, 6):
                (ws2_frames / f"frame_{i:04d}.png").write_bytes(f"job2_frame{i}".encode())
            zip2 = create_zip(ws2_frames, target_zip=ws2 / "test_screenshots.zip")
            self.assertEqual(count_frames(ws2_frames), 5)

            # Open zip2 and check exact file list
            from zipfile import ZipFile
            with ZipFile(zip2, "r") as z:
                names = z.namelist()
                self.assertEqual(len(names), 5)
                self.assertEqual(names, [f"frame_{i:04d}.png" for i in range(1, 6)])

    def test_create_zip_contains_extracted_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "frame_0001.png").write_bytes(b"one")
            (folder / "frame_0002.png").write_bytes(b"two")
            archive = create_zip(folder)
            self.assertTrue(archive.exists())
            self.assertEqual(archive.name, folder.name + ".zip")

    def test_parse_ffmpeg_progress_returns_percentage(self):
        self.assertEqual(parse_ffmpeg_progress("frame=  120 fps=30 time=00:01:00.00"), 50)
        self.assertIsNone(parse_ffmpeg_progress("random noise"))

    def test_output_folder_is_remembered(self):
        original = gui_core.SETTINGS_FILE
        with tempfile.TemporaryDirectory() as tmp:
            gui_core.SETTINGS_FILE = Path(tmp) / "settings.json"
            save_output_folder("C:/Videos/frames")
            self.assertEqual(load_output_folder(), "C:/Videos/frames")
        gui_core.SETTINGS_FILE = original

    # --- Error Classification Tests ---

    def test_classify_error_recognizes_common_issues(self):
        self.assertIn("403 Forbidden", classify_error("HTTP Error 403: Forbidden"))
        self.assertIn("私人影片", classify_error("This video is a private video. Sign in to view"))
        self.assertIn("不存在或已被移除", classify_error("ERROR: Video unavailable 404"))
        self.assertIn("硬碟儲存空間不足", classify_error("No space left on device"))
        self.assertIn("存取被拒", classify_error("Permission denied: 'C:\\test'"))
        self.assertIn("網路連線失敗", classify_error("Network connection timed out"))
        self.assertIn("Deno", classify_error("yt-dlp requested js-runtimes deno"))
        self.assertIn("FFmpeg", classify_error("ffmpeg returned exit code 1"))

    # --- Summary Formatter ---

    def test_format_summary(self):
        summary = format_summary(elapsed_seconds=92.5, frame_count=38, has_mp4=True, has_mp3=False, has_zip=True)
        self.assertIn("1 分 32 秒", summary)
        self.assertIn("38 張", summary)
        self.assertIn("MP4 影片：已儲存", summary)
        self.assertIn("MP3 音訊：未選擇", summary)
        self.assertIn("圖片 ZIP：已建立", summary)

    # --- Safe Output Directory & Video ID Tests ---

    def test_extract_video_id(self):
        from gui_core import extract_video_id
        self.assertEqual(extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ"), "dQw4w9WgXcQ")
        self.assertEqual(extract_video_id("https://youtu.be/dQw4w9WgXcQ?t=10"), "dQw4w9WgXcQ")
        self.assertEqual(extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ"), "dQw4w9WgXcQ")
        self.assertIsNone(extract_video_id("https://example.com/video.mp4"))

    def test_get_safe_output_dir_allocates_fresh_and_sequential_dirs(self):
        from gui_core import get_safe_output_dir
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            # 1. Fresh directory
            d1 = get_safe_output_dir(base, "Test Video", "abc12345678")
            self.assertEqual(d1.name, "Test Video [abc12345678]")
            d1.mkdir()
            (d1 / "important_file.txt").write_text("do not touch")

            # 2. Same video processed again: must allocate (2) without touching d1
            d2 = get_safe_output_dir(base, "Test Video", "abc12345678")
            self.assertEqual(d2.name, "Test Video [abc12345678] (2)")
            d2.mkdir()

            # 3. Processed third time: must allocate (3)
            d3 = get_safe_output_dir(base, "Test Video", "abc12345678")
            self.assertEqual(d3.name, "Test Video [abc12345678] (3)")

            # Verify existing data untouched
            self.assertTrue((d1 / "important_file.txt").exists())
            self.assertEqual((d1 / "important_file.txt").read_text(), "do not touch")

    def test_tools_manifest_integrity(self):
        import json
        manifest_path = Path(__file__).parent / "scripts" / "tools_manifest.json"
        self.assertTrue(manifest_path.is_file(), "tools_manifest.json must exist")
        data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        for tool in ("yt-dlp", "deno", "ffmpeg"):
            self.assertIn(tool, data)
            self.assertTrue(data[tool]["version"])
            self.assertTrue(data[tool]["url"].startswith("https://"))
            self.assertEqual(len(data[tool]["sha256"]), 64, f"Invalid SHA-256 length for {tool}")

    # --- Process Killing Pure Logic ---

    def test_kill_process_tree_handles_none_and_terminated(self):
        kill_process_tree(None)
        mock_proc = MagicMock()
        mock_proc.poll.return_value = 0
        kill_process_tree(mock_proc)
        mock_proc.kill.assert_not_called()


if __name__ == "__main__":
    unittest.main()

