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

# Video Screenshot Extractor v2.7.0

v2.7.0 是一次以「一般使用者可直接安裝使用」為目標的重大更新。

本版本已將主要執行環境與外部工具整合進程式套件中，使用者不再需要自行安裝 FFmpeg、ffprobe、yt-dlp、Deno 或設定 PATH。

## 主要更新

### 一鍵安裝，免手動安裝相依工具

v2.7.0 已內建：

- FFmpeg / ffprobe
- yt-dlp
- Deno

一般使用者下載安裝版後即可直接使用，不需要再自行安裝上述工具，也不需要另外設定環境變數或 PATH。

目前內建版本：

- FFmpeg Essentials 9.0.1
- yt-dlp 2026.08.19
- Deno 2.9.6

### 新增正式 Windows 安裝版

新增：

- `VideoScreenshotExtractor-Setup-v2.7.0.exe`

可透過標準 Windows 安裝程序完成安裝，並建立開始功能表捷徑。

安裝後即可直接使用，不需要 Python 環境。

### 新增 Portable 免安裝版

新增：

- `VideoScreenshotExtractor-Portable-v2.7.0.zip`

解壓縮後即可直接執行，適合不想安裝程式或希望放在隨身碟使用的使用者。

## 輸出與檔案管理改善

### 不再覆蓋舊任務

同一支影片重複執行時，現在會自動建立新的輸出資料夾，例如：

```text
影片名稱 [video_id]
影片名稱 [video_id] (2)
影片名稱 [video_id] (3)

## 📄 第三方元件與授權 (Third-Party Notices)

本工具隨附或整合之開源元件：
* **FFmpeg / ffprobe**: LGPL v2.1+ / GPL v3 (Gyan.dev builds)
* **yt-dlp**: The Unlicense
* **Deno**: MIT License
* **Python**: PSF License

詳細授權條款與原始碼來源請參閱 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

> **重要聲明**：本工具僅供使用者處理具有合法存取權限之公開內容。程式不會且不具備繞過會員限制、付費牆、帳號登入或 DRM 數位版權保護機制之功能。
