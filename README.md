# 影片配圖擷取器 (Video Screenshot Extractor)

![Version](https://img.shields.io/badge/version-2.7.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

專為 Windows 設計的桌面 GUI 工具，用於下載公開影片並自動擷取場景切換（Scene Change）配圖。

---

## ✨ 核心特色

* **開箱即用**：正式安裝版隨附完整執行元件（FFmpeg、ffprobe、yt-dlp、Deno），**無需自行安裝 Python、無須手動設定 Windows PATH**。
* **原生乾淨 GUI**：背景執行所有子程序，徹底消除黑色 CMD / Console 彈出視窗。
* **智慧畫面偵測**：依場景變化自動偵測截圖，可自行調整敏感度數值（數值越低截取越密集）。
* **多功能輸出**：
  * 高畫質 PNG 截圖序列（編號如 `frame_0001.png`，不限張數）
  * 自動打包乾淨的圖片 ZIP 壓縮檔
  * 可選下載並合併高畫質 MP4 影片
  * 可選轉檔為高音質 MP3 音訊
* **獨立任務整理**：成果依照「影片標題」建立專屬資料夾，同名影片重新處理時絕不混入舊圖。
* **進度與控制**：
  * 多階段進度百分比與狀態提示
  * 支援**隨時取消處理**，確實終止背景處理程序並清除暫存，不留殭屍進程
  * 處理完成後一鍵「**開啟輸出資料夾**」並顯示處理摘要

---

## 📥 一般使用者安裝與使用

1. 至 [GitHub Releases](../../releases) 下載最新版安裝程式：
   `VideoScreenshotExtractor-Setup-v2.7.0.exe`
2. 雙擊執行安裝程式（不需系統管理員密碼）。
3. 從桌面或開始功能表點擊「**影片配圖擷取器**」開啟。
4. 貼上公開影片網址，勾選所需的輸出項目，點擊「**開始處理**」即可！

---

## 🛠️ 開發與原始碼執行

若要在 Python 開發環境中執行：

### 需求
* Windows 10 / 11
* Python 3.10+
* 系統環境有 `ffmpeg`、`ffprobe`、`yt-dlp`（或將二進位檔置於專案 `tools/` 目錄下）

### 執行
```powershell
python app.py
```

### 執行單元測試
```powershell
python -m unittest -v test_gui_core.GuiCoreTests
```

---

## 📦 打包與建置 (Build & Packaging)

本專案提供一鍵式自動化建置腳本：

1. **準備執行元件**（官方固定版本）：
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\fetch-tools.ps1
   ```
   *此腳本會自動下載並校驗官方釋出的 FFmpeg、ffprobe、yt-dlp、Deno 至 `tools/` 目錄。*

2. **建置應用程式與安裝程式**：
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1 -BuildInstaller
   ```
   *將執行單元測試、以 PyInstaller 產出 onedir 免安裝目錄，並呼叫 Inno Setup 編譯安裝程式。*

---

## 📄 第三方元件與授權 (Third-Party Notices)

本工具隨附或整合之開源元件：
* **FFmpeg / ffprobe**: LGPL v2.1+ / GPL v3 (Gyan.dev builds)
* **yt-dlp**: The Unlicense
* **Deno**: MIT License
* **Python**: PSF License

詳細授權條款與原始碼來源請參閱 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

> **重要聲明**：本工具僅供使用者處理具有合法存取權限之公開內容。程式不會且不具備繞過會員限制、付費牆、帳號登入或 DRM 數位版權保護機制之功能。
