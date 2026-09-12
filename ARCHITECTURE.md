# Video Screenshot Extractor｜ARCHITECTURE

本文件是 `video-screenshot-extractor` 的維護文件。完整功能清單與版本資訊請先查看同一資料夾的 `README.md`。

## 分層概念

- **入口層**：啟動腳本、GUI 或主程式。
- **核心層**：Python 3.12+；ffmpeg／ffprobe；yt-dlp 所提供的主要處理流程。
- **資料層**：設定、快取、輸入與輸出檔案。
- **整合層**：外部工具、模型、平台 API 或打包工具。

## 安全與輸入處理設計 (Security & Sanitization Design)

- **Filename & Path Sanitization**：使用 `sanitize_task_name` 過濾檔名與目錄名稱中的 Windows 不合法字元（`<>:"/\|?*`）與控制字元，降低路徑遍歷（path traversal）風險。
- **Subprocess Argument-List Execution (No shell=True)**：所有外部工具呼叫（yt-dlp, ffmpeg, ffprobe, deno）嚴格使用陣列清單（`list[str]`）傳遞參數，一律禁止 `shell=True`，達成 command injection risk reduction。
- **安全邊界說明**：本專案為本地桌面工具，處理的是本機檔案與外部多媒體資料，不含 LLM/Prompt 處理邏輯，不提供亦不聲稱 Prompt Injection 防護。

## 修改原則

先定位入口，再追到實際處理函式；保持資料格式相容；每次只改一個責任範圍並做最小回歸測試。
