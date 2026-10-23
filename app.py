from __future__ import annotations

import os
import queue
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from gui_core import (
    FRAME_FILE_PATTERN,
    check_runtime_tools,
    classify_error,
    cleanup_job_workspace,
    count_frames,
    create_job_workspace,
    create_zip,
    detect_platform,
    extract_video_id,
    extract_url_from_input,
    format_summary,
    get_safe_output_dir,
    kill_process_tree,
    load_output_folder,
    parse_ffmpeg_progress,
    popen_silent,
    resolve_task_name,
    resolve_ytdlp_plugin_dir,
    build_download_args,
    save_output_folder,
)
from version import APP_NAME_ZH, VERSION

DOWNLOAD_ATTEMPTS = 3


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME_ZH} v{VERSION}")
        icon_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        icon_path = icon_root / "assets" / "morandi" / "app-icon.png"
        if icon_path.is_file():
            self._app_icon = tk.PhotoImage(file=str(icon_path))
            self.iconphoto(True, self._app_icon)
        self.geometry("900x680")
        self.minsize(760, 580)

        self.app_dir = Path(sys.executable if getattr(sys, "frozen", False) else __file__).parent
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.saved_output = load_output_folder()
        self.ytdlp_plugin_dir = resolve_ytdlp_plugin_dir(self.app_dir)

        self.active_process: subprocess.Popen | None = None
        self.is_cancelled = False
        self.job_running = False
        self.active_workspace: Path | None = None
        self.last_task_dir: Path | None = None
        self.url_rows: list[dict[str, object]] = []
        self.pending_jobs: list[tuple[str, str]] = []
        self.batch_choices: tuple[bool, bool, bool, float, str | None] | None = None
        self.batch_tools: dict[str, str | None] | None = None
        self.batch_output: Path | None = None
        self.batch_total = 0
        self.batch_completed = 0
        self.batch_successes = 0
        self.batch_failures = 0
        self.current_job_number = 0

        self.build_ui()
        self.after(100, self.poll_events)

    def build_ui(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(8, weight=1)

        # Row 0: one URL/share-text field per queued job
        jobs_box = ttk.LabelFrame(self, text="下載工作（每列一個網址或一段分享文字）")
        jobs_box.grid(row=0, column=0, columnspan=3, padx=12, pady=8, sticky="ew")
        jobs_box.columnconfigure(0, weight=1)
        self.url_rows_frame = ttk.Frame(jobs_box)
        self.url_rows_frame.grid(row=0, column=0, padx=8, pady=(6, 2), sticky="ew")
        self.url_rows_frame.columnconfigure(1, weight=1)
        self.add_job_button = ttk.Button(jobs_box, text="＋ 新增工作欄位", command=self.add_url_row)
        self.add_job_button.grid(row=1, column=0, padx=8, pady=(2, 7), sticky="w")
        self.add_url_row()

        # Row 1: Output Folder
        ttk.Label(self, text="輸出資料夾").grid(row=1, column=0, padx=12, pady=5, sticky="w")
        self.output = ttk.Entry(self)
        default_dir = self.saved_output or str(Path.home() / "Videos" / "extracted-frames")
        self.output.insert(0, default_dir)
        self.output.grid(row=1, column=1, padx=12, pady=5, sticky="ew")
        ttk.Button(self, text="選擇…", command=self.choose_output).grid(row=1, column=2, padx=12, pady=5)

        # Row 2: Task Name
        ttk.Label(self, text="輸出名稱").grid(row=2, column=0, padx=12, pady=5, sticky="w")
        self.auto_name = tk.BooleanVar(value=True)
        self.name = ttk.Entry(self)
        self.name.grid(row=2, column=1, padx=12, pady=5, sticky="ew")
        ttk.Checkbutton(self, text="自動使用影片標題", variable=self.auto_name).grid(row=2, column=2, padx=12, pady=5)

        # Row 3: Sensitivity
        ttk.Label(self, text="敏感度").grid(row=3, column=0, padx=12, pady=5, sticky="w")
        sens_frame = ttk.Frame(self)
        sens_frame.grid(row=3, column=1, columnspan=2, padx=12, pady=5, sticky="w")
        self.threshold = ttk.Spinbox(sens_frame, from_=0.05, to=0.8, increment=0.01, width=8)
        self.threshold.set("0.18")
        self.threshold.pack(side="left")
        ttk.Label(sens_frame, text=" (數值越低，擷取的畫面越多，預設 0.18)").pack(side="left", padx=8)

        # Row 4: Output formats
        options = ttk.Frame(self)
        options.grid(row=4, column=0, columnspan=3, padx=12, pady=6, sticky="w")
        self.images = tk.BooleanVar(value=True)
        self.mp4 = tk.BooleanVar(value=False)
        self.mp3 = tk.BooleanVar(value=False)
        ttk.Checkbutton(options, text="提取圖片 (PNG + ZIP)", variable=self.images).pack(side="left", padx=(0, 18))
        ttk.Checkbutton(options, text="下載 MP4", variable=self.mp4).pack(side="left", padx=(0, 18))
        ttk.Checkbutton(options, text="下載 MP3", variable=self.mp3).pack(side="left")

        # Row 5: Action buttons
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=5, column=0, columnspan=3, padx=12, pady=8)
        self.start_button = ttk.Button(btn_frame, text="開始處理", command=self.start)
        self.start_button.pack(side="left", padx=6)
        self.cancel_button = ttk.Button(btn_frame, text="取消處理", command=self.cancel, state="disabled")
        self.cancel_button.pack(side="left", padx=6)
        self.open_button = ttk.Button(btn_frame, text="開啟輸出資料夾", command=self.open_output_folder, state="disabled")
        self.open_button.pack(side="left", padx=6)

        # Row 6: Progress
        self.progress = ttk.Progressbar(self, maximum=100)
        self.progress.grid(row=6, column=0, columnspan=2, padx=12, pady=4, sticky="ew")
        self.progress_label = ttk.Label(self, text="0%")
        self.progress_label.grid(row=6, column=2, padx=12, pady=4, sticky="e")

        # Row 7: Status
        self.status = ttk.Label(self, text="等待開始", font=("TkDefaultFont", 9, "bold"))
        self.status.grid(row=7, column=0, columnspan=3, padx=12, pady=3, sticky="w")

        # Row 8: Log Textbox
        self.log = tk.Text(self, height=14, state="disabled", wrap="word")
        self.log.grid(row=8, column=0, columnspan=3, padx=12, pady=6, sticky="nsew")

    def add_url_row(self, value: str = "") -> None:
        row_frame = ttk.Frame(self.url_rows_frame)
        row_frame.grid(column=0, columnspan=5, sticky="ew", pady=3)
        row_frame.columnconfigure(1, weight=1)

        number_label = ttk.Label(row_frame, width=7)
        number_label.grid(row=0, column=0, padx=(0, 6), sticky="w")
        entry = ttk.Entry(row_frame)
        entry.grid(row=0, column=1, sticky="ew")
        platform_text = tk.StringVar(value="平台：等待網址")
        ttk.Label(row_frame, textvariable=platform_text, width=22).grid(row=0, column=2, padx=8, sticky="w")

        row: dict[str, object] = {
            "frame": row_frame,
            "number": number_label,
            "entry": entry,
            "platform_text": platform_text,
        }
        paste_button = ttk.Button(row_frame, text="貼上", width=7, command=lambda: self.paste_url(row))
        paste_button.grid(row=0, column=3, padx=(0, 5))
        remove_button = ttk.Button(row_frame, text="移除", width=7, command=lambda: self.remove_url_row(row))
        remove_button.grid(row=0, column=4)
        row["paste_button"] = paste_button
        row["remove_button"] = remove_button
        entry.bind("<KeyRelease>", lambda _event: self.update_platform_hint(row))
        if value:
            entry.insert(0, value)
        self.url_rows.append(row)
        self.refresh_url_rows()
        self.update_platform_hint(row)
        entry.focus_set()

    def remove_url_row(self, row: dict[str, object]) -> None:
        if self.job_running:
            return
        if len(self.url_rows) == 1:
            entry = row["entry"]
            assert isinstance(entry, ttk.Entry)
            entry.delete(0, tk.END)
            self.update_platform_hint(row)
            return
        frame = row["frame"]
        assert isinstance(frame, ttk.Frame)
        frame.destroy()
        self.url_rows.remove(row)
        self.refresh_url_rows()

    def refresh_url_rows(self) -> None:
        for index, row in enumerate(self.url_rows, start=1):
            frame = row["frame"]
            number = row["number"]
            remove_button = row["remove_button"]
            assert isinstance(frame, ttk.Frame)
            assert isinstance(number, ttk.Label)
            assert isinstance(remove_button, ttk.Button)
            frame.grid(row=index - 1)
            number.configure(text=f"工作 {index}")
            remove_button.configure(state="normal" if len(self.url_rows) > 1 else "disabled")

    def set_url_controls_state(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.add_job_button.configure(state=state)
        for row in self.url_rows:
            for key in ("entry", "paste_button", "remove_button"):
                widget = row[key]
                assert isinstance(widget, ttk.Widget)
                widget.configure(state=state)
        if enabled:
            self.refresh_url_rows()

    def choose_output(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.output.delete(0, tk.END)
            self.output.insert(0, folder)
            save_output_folder(folder)

    def paste_url(self, row: dict[str, object]) -> None:
        try:
            entry = row["entry"]
            assert isinstance(entry, ttk.Entry)
            entry.delete(0, tk.END)
            entry.insert(0, self.clipboard_get())
            self.update_platform_hint(row)
        except tk.TclError:
            messagebox.showwarning("剪貼簿沒有網址", "請先複製影片網址")

    def update_platform_hint(self, row: dict[str, object]) -> None:
        entry = row["entry"]
        platform_text = row["platform_text"]
        assert isinstance(entry, ttk.Entry)
        assert isinstance(platform_text, tk.StringVar)
        value = entry.get().strip()
        if not value:
            platform_text.set("平台：等待網址")
            return
        try:
            url = extract_url_from_input(value)
        except ValueError as exc:
            hint = "偵測到多個網址" if "偵測到" in str(exc) else "等待有效 HTTP(S) 網址"
            platform_text.set(f"平台：{hint}")
            return
        platform_text.set(f"平台：{detect_platform(url)}")

    def open_output_folder(self) -> None:
        target = self.last_task_dir or Path(self.output.get().strip())
        if target.exists():
            try:
                if sys.platform == "win32":
                    os.startfile(str(target))
                else:
                    subprocess.run(["xdg-open", str(target)])
            except Exception as e:
                messagebox.showerror("無法開啟資料夾", f"開啟失敗：{e}")
        else:
            messagebox.showwarning("資料夾不存在", f"路徑不存在：{target}")

    def write_log(self, line: str) -> None:
        self.log.configure(state="normal")
        self.log.insert(tk.END, line + "\n")
        self.log.see(tk.END)
        self.log.configure(state="disabled")

    def cancel(self) -> None:
        if not self.is_cancelled:
            self.is_cancelled = True
            self.cancel_button.configure(state="disabled")
            self.events.put(("log", "【使用者已觸發取消】正在終止相關程序並清理暫存檔…"))
            self.events.put(("status", "正在取消中…"))
            kill_process_tree(self.active_process)

    def start(self) -> None:
        if self.job_running:
            return

        try:
            threshold = float(self.threshold.get())
        except ValueError:
            messagebox.showwarning("敏感度格式錯誤", "請輸入有效的敏感度數值。")
            return

        jobs: list[tuple[str, str]] = []
        validation_errors: list[str] = []
        for index, row in enumerate(self.url_rows, start=1):
            entry = row["entry"]
            platform_text = row["platform_text"]
            assert isinstance(entry, ttk.Entry)
            assert isinstance(platform_text, tk.StringVar)
            raw_input = entry.get().strip()
            if not raw_input:
                continue
            try:
                url = extract_url_from_input(raw_input)
            except ValueError as exc:
                validation_errors.append(f"工作 {index}：{exc}")
                self.update_platform_hint(row)
                continue
            platform = detect_platform(url)
            entry.delete(0, tk.END)
            entry.insert(0, url)
            platform_text.set(f"平台：{platform}")
            jobs.append((url, platform))

        if not jobs and not validation_errors:
            messagebox.showwarning("缺少網址", "請至少建立一個工作並貼上影片網址或分享文字")
            return
        if validation_errors:
            messagebox.showwarning("網址格式錯誤", "\n".join(validation_errors))
            return
        if not any((self.images.get(), self.mp4.get(), self.mp3.get())):
            messagebox.showwarning("尚未選擇輸出", "至少勾選一種輸出格式（擷取圖片、MP4、MP3）")
            return
        if not self.auto_name.get() and not self.name.get().strip():
            messagebox.showwarning("缺少輸出名稱", "請輸入手動輸出名稱，或勾選自動使用影片標題")
            return
        if len(jobs) > 1 and not self.auto_name.get():
            messagebox.showwarning("多工作命名衝突", "多個工作請使用自動影片標題；手動名稱只適用單一工作。")
            return

        output = Path(self.output.get().strip())
        tools = check_runtime_tools(self.app_dir)
        missing_required = []
        if not tools["ffmpeg"]:
            missing_required.append("• FFmpeg (ffmpeg.exe)")
        if not tools["ffprobe"]:
            missing_required.append("• FFprobe (ffprobe.exe)")
        if not tools["yt-dlp"]:
            missing_required.append("• yt-dlp (yt-dlp.exe)")
        if missing_required:
            messagebox.showerror(
                "缺少必要執行元件",
                "找不到以下必要元件，無法進行影片下載或分析：\n\n"
                + "\n".join(missing_required)
                + "\n\n正式安裝版請確認 tools/ 目錄是否完整；開發模式請確認已安裝並加入系統 PATH。",
            )
            return

        save_output_folder(str(output))
        self.is_cancelled = False
        self.job_running = True
        self.pending_jobs = list(jobs)
        self.batch_total = len(jobs)
        self.batch_completed = 0
        self.batch_successes = 0
        self.batch_failures = 0
        self.batch_output = output
        self.batch_tools = tools
        self.batch_choices = (
            self.images.get(),
            self.mp4.get(),
            self.mp3.get(),
            threshold,
            self.name.get().strip() if not self.auto_name.get() else None,
        )
        self.start_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.open_button.configure(state="disabled")
        self.set_url_controls_state(False)
        self.progress["value"] = 0
        self.progress_label.configure(text="0%")
        self.write_log(f"已建立 {self.batch_total} 個工作，將依序處理。")
        self.start_next_job()

    def start_next_job(self) -> None:
        if self.is_cancelled or not self.pending_jobs:
            return
        assert self.batch_output is not None
        assert self.batch_choices is not None
        assert self.batch_tools is not None
        url, platform = self.pending_jobs.pop(0)
        self.current_job_number = self.batch_completed + 1
        self.progress["value"] = 0
        self.progress_label.configure(text="0%")
        self.write_log("")
        self.write_log(f"[工作 {self.current_job_number}/{self.batch_total}] 平台：{platform}")
        threading.Thread(
            target=self.worker,
            args=(url, self.batch_output, self.batch_choices, self.batch_tools),
            daemon=True,
        ).start()

    def _register_process(self, proc: subprocess.Popen | None) -> None:
        self.active_process = proc
        if proc is not None and self.is_cancelled:
            kill_process_tree(proc)

    def _wait_for_process(self, proc: subprocess.Popen) -> int:
        if self.is_cancelled:
            kill_process_tree(proc)
        try:
            return proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            kill_process_tree(proc)
            proc.kill()
            return proc.wait(timeout=5)

    def worker(
        self,
        url: str,
        output: Path,
        choices: tuple[bool, bool, bool, float, str | None],
        tools: dict[str, str | None],
    ) -> None:
        images, mp4, mp3, threshold, manual_name = choices
        start_time = time.time()
        workspace: Path | None = None

        downloader_bin = tools["yt-dlp"]
        ffmpeg_bin = tools["ffmpeg"]
        ffprobe_bin = tools["ffprobe"]
        deno_bin = tools.get("deno")

        assert downloader_bin is not None
        assert ffmpeg_bin is not None
        assert ffprobe_bin is not None

        try:
            workspace = create_job_workspace()
            self.active_workspace = workspace
            source = workspace / "source.mp4"
            frames_dir = workspace / "frames"

            # Stage 1: Resolve task title
            self.events.put(("status", "階段 1/5：正在取得影片資訊與標題…"))
            if not deno_bin:
                self.events.put(("log", "提示：未偵測到 Deno 元件，若遇 YouTube JS 驗證可能受限。"))

            if self.is_cancelled:
                raise InterruptedError("已由使用者取消")

            task_name = resolve_task_name(
                [downloader_bin], url, deno_bin, manual_name, self.ytdlp_plugin_dir, ffmpeg_bin,
                on_process=self._register_process, is_cancelled=lambda: self.is_cancelled,
            )
            self.events.put(("log", f"任務標題：{task_name}"))

            # Stage 2: Download video
            if self.is_cancelled:
                raise InterruptedError("已由使用者取消")

            self.events.put(("status", "階段 2/5：正在下載影片 (0%~65%)…"))
            # YouTube intermittently 403s a fetched link; re-running yt-dlp fetches fresh links.
            for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
                download_cmd = build_download_args(
                    [downloader_bin], str(source), url, deno_bin, self.ytdlp_plugin_dir, ffmpeg_bin
                )
                proc = popen_silent(download_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                self._register_process(proc)
                assert proc.stdout is not None

                download_error_lines: list[str] = []
                for line in proc.stdout:
                    if self.is_cancelled:
                        break
                    line = line.rstrip()
                    self.events.put(("log", line))
                    if line:
                        download_error_lines.append(line)
                        download_error_lines = download_error_lines[-8:]
                    if "[download]" in line and "%" in line:
                        try:
                            percent_str = line.split("%", 1)[0].rsplit(" ", 1)[-1]
                            percent = float(percent_str)
                            self.events.put(("progress", percent * 0.65))
                        except ValueError:
                            pass

                ret = self._wait_for_process(proc)
                self.active_process = None
                if self.is_cancelled:
                    raise InterruptedError("已由使用者取消")
                if ret == 0:
                    break
                detail = "\n".join(download_error_lines)
                if attempt < DOWNLOAD_ATTEMPTS and "HTTP Error 403" in detail:
                    self.events.put(("log", f"YouTube 暫時拒絕連結 (403)，重新取得連結再試（{attempt + 1}/{DOWNLOAD_ATTEMPTS}）…"))
                    continue
                raise RuntimeError(detail or f"影片下載失敗，yt-dlp 返回碼：{ret}")

            # Non-destructive target directory under output folder
            video_id = extract_video_id(url)
            task_output_dir = get_safe_output_dir(output, task_name, video_id)
            task_output_dir.mkdir(parents=True, exist_ok=True)
            self.last_task_dir = task_output_dir
            self.events.put(("log", f"成果輸出目錄：{task_output_dir}"))

            # Stage 3: MP4 and/or MP3 export
            self.events.put(("status", "階段 3/5：正在處理音訊與影片輸出…"))
            if mp4:
                if self.is_cancelled:
                    raise InterruptedError("已由使用者取消")
                target_mp4 = task_output_dir / f"{task_name}.mp4"
                shutil.copy2(source, target_mp4)
                self.events.put(("log", f"✓ MP4 影片已儲存至：{target_mp4}"))

            if mp3:
                if self.is_cancelled:
                    raise InterruptedError("已由使用者取消")
                target_mp3 = task_output_dir / f"{task_name}.mp3"
                mp3_cmd = [ffmpeg_bin, "-y", "-i", str(source), "-vn", "-q:a", "2", str(target_mp3)]
                proc = popen_silent(mp3_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                self._register_process(proc)
                _, err = proc.communicate()
                self.active_process = None
                if self.is_cancelled:
                    raise InterruptedError("已由使用者取消")
                if proc.returncode != 0:
                    raise RuntimeError(f"MP3 轉檔失敗：{err}")
                self.events.put(("log", f"✓ MP3 音訊已儲存至：{target_mp3}"))

            # Stage 4: Scene-change extraction
            frame_count = 0
            has_zip = False
            if images:
                if self.is_cancelled:
                    raise InterruptedError("已由使用者取消")
                self.events.put(("status", "階段 4/5：正在分析影片時長與畫面切換 (65%~95%)…"))

                # Get duration with ffprobe
                probe_cmd = [
                    ffprobe_bin,
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(source),
                ]
                proc = popen_silent(probe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                out, err = proc.communicate()
                if proc.returncode != 0 or not out.strip():
                    duration = 120.0
                else:
                    try:
                        duration = float(out.strip())
                    except ValueError:
                        duration = 120.0

                frame_target_spec = str(frames_dir / FRAME_FILE_PATTERN)
                extract_cmd = [
                    ffmpeg_bin,
                    "-y",
                    "-hide_banner",
                    "-loglevel", "error",
                    "-i", str(source),
                    "-vf", f"select='gt(scene,{threshold})'",
                    "-progress", "pipe:1",
                    "-fps_mode", "passthrough",
                    frame_target_spec,
                ]
                proc = popen_silent(extract_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                self._register_process(proc)
                assert proc.stdout is not None

                for line in proc.stdout:
                    if self.is_cancelled:
                        break
                    p = parse_ffmpeg_progress(line, duration)
                    if p is not None:
                        self.events.put(("progress", 65 + p * 0.30))
                    current_count = count_frames(frames_dir)
                    if current_count:
                        self.events.put(("status", f"階段 4/5：偵測切換中…目前已擷取 {current_count} 張圖片"))

                ret = self._wait_for_process(proc)
                self.active_process = None
                if self.is_cancelled:
                    raise InterruptedError("已由使用者取消")
                if ret != 0:
                    raise RuntimeError(f"圖片擷取失敗，FFmpeg 返回碼：{ret}")

                frame_count = count_frames(frames_dir)
                self.events.put(("log", f"✓ 畫面分析完成，共擷取 {frame_count} 張圖片。"))

                # Stage 5: Pack ZIP & Move Screenshots
                self.events.put(("status", "階段 5/5：正在建立圖片 ZIP 壓縮檔與整理輸出目錄…"))
                target_zip = task_output_dir / f"{task_name}_screenshots.zip"
                create_zip(frames_dir, frame_prefix="frame_", target_zip=target_zip)
                has_zip = True
                self.events.put(("log", f"✓ 圖片 ZIP 壓縮檔已建立：{target_zip}"))

                # Move clean frames to output directory screenshots subfolder
                target_screenshots_dir = task_output_dir / "screenshots"
                if not target_screenshots_dir.exists():
                    shutil.copytree(frames_dir, target_screenshots_dir)
                else:
                    target_screenshots_dir.mkdir(parents=True, exist_ok=True)
                    for frame_file in frames_dir.glob("*.png"):
                        shutil.copy2(frame_file, target_screenshots_dir / frame_file.name)
                self.events.put(("log", f"✓ 圖片已整理至：{target_screenshots_dir}"))

            self.events.put(("progress", 100))
            elapsed = time.time() - start_time
            summary_text = format_summary(elapsed, frame_count, mp4, mp3, has_zip)
            self.events.put(("success", {"summary": summary_text, "dir": task_output_dir}))

        except InterruptedError:
            self.events.put(("cancelled", None))
        except Exception as exc:
            user_msg = classify_error(exc)
            self.events.put(("error", {"user_msg": user_msg, "raw_error": str(exc)}))
        finally:
            cleanup_job_workspace(workspace)
            self.active_workspace = None
            self.active_process = None
            self.events.put(("done", None))

    def finish_batch(self, cancelled: bool = False) -> None:
        self.job_running = False
        self.pending_jobs.clear()
        self.start_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        self.set_url_controls_state(True)
        if cancelled:
            self.status.configure(text=f"已取消；停止於工作 {self.batch_completed}/{self.batch_total}")
        else:
            self.status.configure(
                text=f"全部工作結束：成功 {self.batch_successes}，失敗 {self.batch_failures}"
            )
            self.write_log(
                f"批次結果：共 {self.batch_total} 個工作，成功 {self.batch_successes}，失敗 {self.batch_failures}。"
            )

    def poll_events(self) -> None:
        while not self.events.empty():
            kind, value = self.events.get()
            if kind == "log":
                self.write_log(str(value))
            elif kind == "progress":
                val = float(value)
                self.progress["value"] = val
                self.progress_label.configure(text=f"{val:.1f}%")
            elif kind == "status":
                self.status.configure(text=str(value))
            elif kind == "success":
                data = value if isinstance(value, dict) else {}
                summary = data.get("summary", "處理完成！")
                self.batch_successes += 1
                self.status.configure(text="處理完成！")
                self.write_log("\n==========================================")
                self.write_log(summary)
                self.write_log("==========================================\n")
                self.open_button.configure(state="normal")
            elif kind == "cancelled":
                self.status.configure(text="已取消處理")
                self.write_log("【已取消】已終止執行程序並清理暫存檔案。")
            elif kind == "error":
                data = value if isinstance(value, dict) else {}
                user_msg = data.get("user_msg", "處理失敗")
                raw_error = data.get("raw_error", "")
                self.batch_failures += 1
                self.status.configure(text=f"錯誤：{user_msg}")
                self.write_log(f"【錯誤】{user_msg}")
                if raw_error:
                    self.write_log(f"詳細錯誤訊息：{raw_error}")
                messagebox.showerror(f"工作 {self.current_job_number} 處理失敗", user_msg)
            elif kind == "done":
                self.batch_completed += 1
                if self.is_cancelled:
                    self.finish_batch(cancelled=True)
                elif self.pending_jobs:
                    self.start_next_job()
                else:
                    self.finish_batch()

        self.after(100, self.poll_events)


if __name__ == "__main__":
    App().mainloop()

