import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import gui_core
from gui_core import build_download_args, clear_source_work_files, create_zip, find_deno, find_ytdlp, load_output_folder, parse_ffmpeg_progress, resolve_task_name, sanitize_task_name, save_output_folder


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
        with patch("gui_core.subprocess.run", return_value=result) as run:
            self.assertEqual(resolve_task_name(["yt-dlp"], "url", r"C:\deno.exe"), "Title")
            run.assert_called_once()

    def test_find_ytdlp_from_path(self):
        with patch("shutil.which", return_value=r"C:\tools\yt-dlp.exe"):
            self.assertEqual(find_ytdlp(), r"C:\tools\yt-dlp.exe")

    def test_find_ytdlp_from_localappdata(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Programs/Python/Python313/Scripts/yt-dlp.exe"
            path.parent.mkdir(parents=True)
            path.touch()
            with patch.dict("os.environ", {"LOCALAPPDATA": tmp, "APPDATA": ""}, clear=False), patch("shutil.which", return_value=None):
                self.assertEqual(find_ytdlp(), str(path))

    def test_find_ytdlp_from_appdata(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Python/Python313/Scripts/yt-dlp.exe"
            path.parent.mkdir(parents=True)
            path.touch()
            with patch.dict("os.environ", {"LOCALAPPDATA": "", "APPDATA": tmp}, clear=False), patch("shutil.which", return_value=None):
                self.assertEqual(find_ytdlp(), str(path))

    def test_find_ytdlp_missing(self):
        with patch("shutil.which", return_value=None), patch.dict("os.environ", {"LOCALAPPDATA": "", "APPDATA": ""}, clear=False):
            self.assertIsNone(find_ytdlp())

    def test_find_deno_from_path(self):
        with patch("shutil.which", return_value=r"C:\deno.exe"):
            self.assertEqual(find_deno(), r"C:\deno.exe")

    def test_find_deno_from_user_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".deno/bin/deno.exe"
            path.parent.mkdir(parents=True)
            path.touch()
            with patch("shutil.which", return_value=None), patch("pathlib.Path.home", return_value=Path(tmp)):
                self.assertEqual(find_deno(), str(path))

    def test_find_deno_missing(self):
        with patch("shutil.which", return_value=None), patch("pathlib.Path.home", return_value=Path(tempfile.mkdtemp())):
            self.assertIsNone(find_deno())

    def test_parse_ffmpeg_progress_returns_percentage(self):
        self.assertEqual(parse_ffmpeg_progress("frame=  120 fps=30 time=00:01:00.00"), 50)

    def test_create_zip_contains_extracted_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "frame_01.png").write_bytes(b"one")
            (folder / "frame_02.png").write_bytes(b"two")
            archive = create_zip(folder)
            self.assertTrue(archive.exists())
            self.assertEqual(archive.name, folder.name + ".zip")

    def test_output_folder_is_remembered(self):
        original = gui_core.SETTINGS_FILE
        with tempfile.TemporaryDirectory() as tmp:
            gui_core.SETTINGS_FILE = Path(tmp) / "settings.json"
            save_output_folder("C:/Videos/frames")
            self.assertEqual(load_output_folder(), "C:/Videos/frames")
        gui_core.SETTINGS_FILE = original


if __name__ == "__main__":
    unittest.main()
