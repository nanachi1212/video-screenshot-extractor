from __future__ import annotations

import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from gui_core import build_download_args, clear_source_work_files, create_zip, find_deno, find_ytdlp, load_output_folder, parse_ffmpeg_progress, resolve_task_name, save_output_folder


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("影片配圖擷取器 v2.0")
        self.geometry("760x520")
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.saved_output = load_output_folder()
        self.build_ui()
        self.after(100, self.poll_events)

    def build_ui(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(7, weight=1)
        ttk.Label(self, text="影片網址").grid(row=0, column=0, padx=12, pady=10, sticky="w")
        self.url = ttk.Entry(self)
        self.url.grid(row=0, column=1, padx=12, pady=10, sticky="ew")
        ttk.Button(self, text="貼上", command=self.paste_url).grid(row=0, column=2, padx=12, pady=10)
        ttk.Label(self, text="輸出資料夾").grid(row=1, column=0, padx=12, pady=5, sticky="w")
        self.output = ttk.Entry(self)
        self.output.insert(0, self.saved_output or str(Path.home() / "Videos" / "extracted-frames"))
        self.output.grid(row=1, column=1, padx=12, pady=5, sticky="ew")
        ttk.Button(self, text="選擇…", command=self.choose_output).grid(row=1, column=2, padx=12, pady=5)
        ttk.Label(self, text="輸出名稱").grid(row=2, column=0, padx=12, pady=5, sticky="w")
        self.auto_name = tk.BooleanVar(value=True)
        self.name = ttk.Entry(self)
        self.name.grid(row=2, column=1, padx=12, pady=5, sticky="ew")
        ttk.Checkbutton(self, text="自動使用影片標題", variable=self.auto_name).grid(row=2, column=2, padx=12, pady=5)
        ttk.Label(self, text="敏感度").grid(row=3, column=0, padx=12, pady=5, sticky="w")
        self.threshold = ttk.Spinbox(self, from_=0.05, to=0.8, increment=0.01, width=8)
        self.threshold.set("0.18")
        self.threshold.grid(row=3, column=1, padx=12, pady=5, sticky="w")
        ttk.Label(self, text="數值越低，擷取的畫面越多").grid(row=3, column=1, padx=90, pady=5, sticky="w")
        options = ttk.Frame(self)
        options.grid(row=4, column=0, columnspan=3, padx=12, pady=8, sticky="w")
        self.images = tk.BooleanVar(value=True)
        self.mp4 = tk.BooleanVar(value=False)
        self.mp3 = tk.BooleanVar(value=False)
        ttk.Checkbutton(options, text="提取圖片", variable=self.images).pack(side="left", padx=(0, 18))
        ttk.Checkbutton(options, text="下載 MP4", variable=self.mp4).pack(side="left", padx=(0, 18))
        ttk.Checkbutton(options, text="下載 MP3", variable=self.mp3).pack(side="left")
        self.start_button = ttk.Button(self, text="開始處理", command=self.start)
        self.start_button.grid(row=5, column=0, columnspan=3, padx=12, pady=8)
        self.progress = ttk.Progressbar(self, maximum=100)
        self.progress.grid(row=6, column=0, columnspan=2, padx=12, pady=5, sticky="ew")
        self.progress_label = ttk.Label(self, text="0%")
        self.progress_label.grid(row=6, column=2, padx=12, pady=5, sticky="e")
        self.status = ttk.Label(self, text="等待開始")
        self.status.grid(row=7, column=0, columnspan=3, padx=12, pady=3, sticky="w")
        self.log = tk.Text(self, height=16, state="disabled")
        self.log.grid(row=8, column=0, columnspan=3, padx=12, pady=6, sticky="nsew")

    def choose_output(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.output.delete(0, tk.END)
            self.output.insert(0, folder)
            save_output_folder(folder)

    def paste_url(self) -> None:
        try:
            self.url.delete(0, tk.END)
            self.url.insert(0, self.clipboard_get())
        except tk.TclError:
            messagebox.showwarning("剪貼簿沒有網址", "請先複製影片網址")

    def write_log(self, line: str) -> None:
        self.log.configure(state="normal")
        self.log.insert(tk.END, line + "\n")
        self.log.see(tk.END)
        self.log.configure(state="disabled")

    def start(self) -> None:
        url = self.url.get().strip()
        output = Path(self.output.get().strip())
        if not url:
            messagebox.showwarning("缺少網址", "請貼上影片網址")
            return
        if not any((self.images.get(), self.mp4.get(), self.mp3.get())):
            messagebox.showwarning("未選擇輸出", "至少勾選一種輸出格式")
            return
        if not self.auto_name.get() and not self.name.get().strip():
            messagebox.showwarning("缺少輸出名稱", "請輸入手動輸出名稱，或勾選自動使用影片標題")
            return
        if not shutil.which("ffmpeg"):
            messagebox.showerror("找不到 ffmpeg", "請先安裝 ffmpeg 並加入 PATH")
            return
        if not (downloader := self.downloader()):
            messagebox.showerror("找不到 yt-dlp", "找不到 yt-dlp，請先安裝或更新 yt-dlp。")
            return
        save_output_folder(str(output))
        self.start_button.configure(state="disabled")
        choices = (self.images.get(), self.mp4.get(), self.mp3.get(), float(self.threshold.get()), self.name.get().strip() if not self.auto_name.get() else None)
        threading.Thread(target=self.worker, args=(url, output, choices, downloader), daemon=True).start()

    def downloader(self) -> list[str] | None:
        app_dir = Path(sys.executable if getattr(sys, "frozen", False) else __file__).parent
        path = find_ytdlp(app_dir)
        return [path] if path else None

    def worker(self, url: str, output: Path, choices: tuple[bool, bool, bool, float, str | None], downloader: list[str]) -> None:
        images, mp4, mp3, threshold, manual_name = choices
        try:
            output.mkdir(parents=True, exist_ok=True)
            source = output / "source.mp4"
            clear_source_work_files(source)
            self.events.put(("status", "下載影片中…"))
            deno = find_deno()
            if not deno:
                self.events.put(("log", "警告：未偵測到 Deno，YouTube 部分影片或格式可能無法正常下載。"))
            task_name = resolve_task_name(downloader, url, deno, manual_name)
            command = build_download_args(downloader, str(source), url, deno)
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            assert process.stdout is not None
            for line in process.stdout:
                line = line.rstrip()
                self.events.put(("log", line))
                if "[download]" in line and "%" in line:
                    try:
                        percent = float(line.split("%", 1)[0].rsplit(" ", 1)[-1])
                        self.events.put(("progress", percent * 0.65))
                    except ValueError:
                        pass
            if process.wait() != 0:
                raise RuntimeError("影片下載失敗")
            if mp4:
                target = output / f"{task_name}.mp4"
                shutil.copy2(source, target)
                self.events.put(("log", f"MP4：{target}"))
            if mp3:
                target = output / f"{task_name}.mp3"
                subprocess.run(["ffmpeg", "-y", "-i", str(source), "-vn", "-q:a", "2", str(target)], check=True)
                self.events.put(("log", f"MP3：{target}"))
            if images:
                self.events.put(("status", "偵測畫面切換中…"))
                duration = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(source)], text=True).strip())
                command = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(source), "-vf", f"select='gt(scene,{threshold})'", "-progress", "pipe:1", "-vsync", "0", str(output / f"{task_name}_%02d.png")]
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                assert process.stdout is not None
                for line in process.stdout:
                    percent = parse_ffmpeg_progress(line, duration)
                    if percent is not None:
                        self.events.put(("progress", 65 + percent * 0.35))
                    count = len(list(output.glob("frame_*.png")))
                    if count:
                        self.events.put(("status", f"已輸出 {count} 張圖片…"))
                if process.wait() != 0:
                    raise RuntimeError("圖片擷取失敗")
                archive = create_zip(output, f"{task_name}_")
                named_archive = output / f"{task_name}.zip"
                archive.replace(named_archive)
                self.events.put(("log", f"圖片 ZIP：{named_archive}"))
            self.events.put(("progress", 100))
            self.events.put(("status", "處理完成"))
            clear_source_work_files(source)
        except Exception as exc:
            self.events.put(("log", f"錯誤：{exc}"))
            self.events.put(("status", "處理失敗"))
        finally:
            self.events.put(("done", None))

    def poll_events(self) -> None:
        while not self.events.empty():
            kind, value = self.events.get()
            if kind == "log":
                self.write_log(str(value))
            elif kind == "progress":
                self.progress["value"] = float(value)
                self.progress_label.configure(text=f"{float(value):.1f}%")
            elif kind == "status":
                self.status.configure(text=str(value))
            elif kind == "done":
                self.start_button.configure(state="normal")
        self.after(100, self.poll_events)


if __name__ == "__main__":
    App().mainloop()
