import tempfile
import unittest
from pathlib import Path

from gui_core import build_download_args, create_zip, parse_ffmpeg_progress


class GuiCoreTests(unittest.TestCase):
    def test_download_command_requests_video_and_audio(self):
        args = build_download_args(["yt-dlp"], "source.mp4", "https://example.com/video")
        self.assertIn("bv*+ba/b", args)
        self.assertIn("--merge-output-format", args)

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


if __name__ == "__main__":
    unittest.main()
