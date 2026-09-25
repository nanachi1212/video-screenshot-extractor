# 影片配圖擷取器（Video Screenshot Extractor）

![Latest Release](https://img.shields.io/github/v/release/nanachi1212/video-screenshot-extractor?label=version&color=blue)
![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-brightgreen)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)

一款專為 Windows 設計的桌面 GUI 工具，可下載具有合法存取權限的公開影片（包含公開 Threads、Facebook 與 X / Twitter 影片貼文），並依照畫面場景變化自動擷取代表性截圖。

除了場景截圖之外，也可選擇輸出：

- PNG 圖片
- 圖片 ZIP
- MP4 影片
- MP3 音訊

從 **v2.7.0** 開始，正式版已整合 FFmpeg、ffprobe、yt-dlp 與 Deno。

**一般使用者不需要安裝 Python、不需要自行安裝上述工具，也不需要設定 Windows PATH。**

---

## ✨ 核心特色

### 📦 開箱即用

正式 Windows 版本已整合主要執行元件：

- FFmpeg
- ffprobe
- yt-dlp
- Threads extractor plugin
- Deno
- Python Runtime

一般使用者只需下載安裝版或 Portable 版即可使用。

不需要：

- 自行安裝 Python
- 自行安裝 FFmpeg
- 自行安裝 yt-dlp
- 自行安裝 Deno
- 手動修改 Windows PATH
- 使用 PowerShell 或 CMD 啟動程式

---

### Threads 公開影片下載

可直接貼上公開 Threads 影片貼文網址，例如：

```text
https://www.threads.com/@username/post/POST_ID
https://www.threads.net/@username/post/POST_ID
https://www.threads.com/share/SHARE_CODE/
```

正式版會自動載入隨附的 Threads extractor，不需要另外安裝 plugin。此功能僅處理公開可檢視的影片貼文，不提供登入繞過、私人內容或 DRM 存取。Threads 網站結構若變更，可能需要更新 extractor。

---

### X / Twitter 公開影片下載

可直接貼上公開 X / Twitter 影片貼文網址，例如：

```text
https://x.com/username/status/STATUS_ID
https://twitter.com/username/status/STATUS_ID
```

使用 yt-dlp 內建 Twitter extractor，不需要額外 plugin。此功能以免登入可觀看的公開影片貼文為範圍；受保護帳號、需要登入或不可見的貼文不保證可下載。

---

### 🖼️ 自動場景截圖

利用 FFmpeg 的場景變化偵測，自動從影片中擷取具有代表性的畫面。

使用者可以自行調整場景偵測敏感度。

一般而言：

- 數值較低 → 擷取較多圖片
- 數值較高 → 只保留變化較明顯的畫面

---

### 🎬 多種輸出格式

支援：

- 高畫質 PNG 截圖
- 自動建立圖片 ZIP
- MP4 影片
- MP3 音訊

圖片會依序編號，例如：

```text
frame_0001.png
frame_0002.png
frame_0003.png
...
```

不再限制兩位數編號。

---

### 📁 每個任務獨立整理

每支影片都會建立自己的輸出資料夾。

例如：

```text
影片名稱 [video_id]
```

如果再次處理同一支影片，不會覆蓋舊資料，而是自動建立：

```text
影片名稱 [video_id]
影片名稱 [video_id] (2)
影片名稱 [video_id] (3)
```

因此：

- 不會覆蓋舊成果
- 不會刪除之前的圖片
- 不會把不同任務的圖片混在一起

---

### 🧹 自動清理暫存檔

每次任務都會使用獨立工作目錄。

正常完成後會自動清理暫存資料，例如：

```text
source.mp4
*.part
```

避免暫存檔殘留到正式輸出資料夾。

---

### 📊 進度與任務控制

提供：

- 多階段進度顯示
- 處理狀態提示
- 下載進度
- 截圖處理進度
- 完成摘要
- 取消任務
- 一鍵開啟輸出資料夾

取消任務時，程式會嘗試終止相關背景處理程序，避免殘留 ffmpeg、yt-dlp 等背景進程。

---

### 🪟 無黑色命令列視窗

正式 GUI 版本在背景執行：

- FFmpeg
- ffprobe
- yt-dlp
- Deno

時，不會持續彈出 CMD / Console 黑色視窗。

---

# 📥 下載

請前往：

**[GitHub Releases](https://github.com/nanachi1212/video-screenshot-extractor/releases/latest)**

---

## Windows 安裝版

一般使用者建議下載名稱包含：

```text
VideoScreenshotExtractor-Setup
```

的 `.exe` 安裝程式。

例如目前版本：

```text
VideoScreenshotExtractor-Setup-v2.7.0.exe
```

安裝後可從：

- Windows 開始功能表
- 桌面捷徑（安裝時可選）

直接啟動。

---

## Portable 免安裝版

如果不想安裝程式，可下載名稱包含：

```text
VideoScreenshotExtractor-Portable
```

的 ZIP。

例如：

```text
VideoScreenshotExtractor-Portable-v2.7.0.zip
```

解壓縮後即可使用。

適合：

- 不想安裝程式
- 放在外接硬碟
- 放在隨身碟
- 臨時使用

---

## 不要下載哪一個？

GitHub Release 頁面會自動出現：

```text
Source code (zip)
Source code (tar.gz)
```

這兩個是 GitHub 自動產生的**原始碼壓縮檔**。

一般 Windows 使用者不需要下載它們。

請選擇：

```text
VideoScreenshotExtractor-Setup-...
```

或：

```text
VideoScreenshotExtractor-Portable-...
```

---

# 🚀 使用方式

## 1. 啟動程式

安裝版：

從 Windows 開始功能表開啟：

```text
影片配圖擷取器
```

Portable 版：

直接執行：

```text
VideoScreenshotExtractor.exe
```

---

## 2. 貼上影片網址

將具有合法存取權限的公開影片網址貼入程式。

---

## 3. 選擇輸出內容

依照需要選擇：

- 場景截圖
- 圖片 ZIP
- MP4
- MP3

---

## 4. 設定輸出資料夾

可自行選擇成果儲存位置。

程式會記住最近使用的輸出資料夾。

---

## 5. 開始處理

按下：

```text
開始處理
```

程式會依序進行：

```text
解析影片
↓
下載來源
↓
擷取場景
↓
建立 PNG
↓
建立 ZIP
↓
輸出 MP4 / MP3
↓
清理暫存資料
```

---

# 📂 輸出範例

假設影片名稱為：

```text
Example Video
```

輸出資料夾可能為：

```text
Example Video [abc123]\
│
├─ frame_0001.png
├─ frame_0002.png
├─ frame_0003.png
├─ Example Video [abc123].zip
├─ Example Video [abc123].mp4
└─ Example Video [abc123].mp3
```

實際產生哪些檔案，取決於你在 GUI 中勾選的輸出項目。

---

# 🆕 v2.7.0 主要更新

v2.7.0 是一次以「一般使用者可以直接安裝使用」為主要目標的產品化更新。

主要改善包括：

- 內建 FFmpeg / ffprobe
- 內建 yt-dlp
- 內建 Deno
- 不再要求一般使用者設定 PATH
- 新增正式 Windows Installer
- 新增 Portable 免安裝版
- 改善背景程序執行方式
- 不再彈出黑色 Console 視窗
- 新增取消任務
- 新增一鍵開啟輸出資料夾
- 每個任務使用獨立工作目錄
- 同一影片重新處理時不覆蓋舊成果
- 修正 `source.mp4` 與 `.part` 暫存檔殘留
- 改善錯誤訊息
- 改善進度顯示
- 加入 SHA-256 完整性驗證
- 建立 GitHub Actions 自動建置與 Release 流程
- Windows PowerShell 建置腳本加入 ASCII-only 相容性檢查
- 單元測試提升至 **35 項**

完整更新內容：

**[v2.7.0 Release](https://github.com/nanachi1212/video-screenshot-extractor/releases/tag/v2.7.0)**

版本差異：

**[v2.6.0 → v2.7.0](https://github.com/nanachi1212/video-screenshot-extractor/compare/v2.6.0...v2.7.0)**

---

# 🧩 內建執行元件

目前 v2.7.0 使用：

| 元件 | 版本 | 用途 |
|---|---:|---|
| FFmpeg / ffprobe | 9.0.1 Essentials | 影片解析、轉檔、場景擷取 |
| yt-dlp | 2026.08.19 | 公開影片下載 |
| Deno | 2.9.6 | yt-dlp JavaScript Runtime |
| Python | PyInstaller 打包 Runtime | GUI 與程式邏輯 |

這些元件會隨正式版一起提供。

一般使用者不需要另外安裝。

---

# 🔐 SHA-256 檔案驗證

每個正式 Release 都會提供：

```text
SHA256SUMS.txt
```

可用來確認下載檔案是否完整。

在 Windows PowerShell 中執行：

```powershell
Get-FileHash ".\VideoScreenshotExtractor-Setup-v2.7.0.exe" -Algorithm SHA256
```

將結果與：

```text
SHA256SUMS.txt
```

中的對應值比較。

如果兩者完全相同，代表該檔案與 Release 建置時產生的檔案一致。

---

# ⚠️ Windows / Chrome 安全性提示

目前程式尚未加入商業程式碼簽章。

因此第一次下載或執行時，可能遇到：

- Chrome 顯示下載警告
- Microsoft Defender SmartScreen 顯示未知發行者
- Windows 顯示應用程式安全提示

這不代表程式一定含有惡意內容，而是因為新的、尚未簽章的 EXE 尚未累積 Windows SmartScreen 信譽。

如需確認完整性，可使用同一個 Release 中的：

```text
SHA256SUMS.txt
```

進行驗證。

請務必只從本專案官方 GitHub Release 下載：

**https://github.com/nanachi1212/video-screenshot-extractor/releases**

---

# 🧪 測試

目前核心測試：

```text
35 / 35 PASS
```

可執行：

```powershell
python -m unittest test_gui_core.py
```

測試內容包含：

- 任務名稱清理
- 自動影片標題
- 影片 ID 解析
- 工具搜尋
- bundled tools 優先順序
- yt-dlp 命令建立
- Deno 整合
- 工作目錄建立與清理
- frame 計數
- ZIP 建立
- 舊任務圖片隔離
- 安全輸出資料夾
- ffmpeg 進度解析
- 背景子程序隱藏
- 工具 manifest 驗證
- PowerShell 建置腳本相容性

---

# 🛠️ 從原始碼執行

這一節只提供給開發者。

一般使用者請直接下載 Release。

## 需求

建議：

```text
Windows 10 / Windows 11
Python 3.12
```

建立虛擬環境：

```powershell
python -m venv .venv
```

啟用：

```powershell
.\.venv\Scripts\Activate.ps1
```

更新 pip：

```powershell
python -m pip install --upgrade pip
```

安裝 PyInstaller：

```powershell
pip install pyinstaller
```

---

## 下載固定版本執行工具

執行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\fetch-tools.ps1
```

腳本會下載：

- FFmpeg
- ffprobe
- yt-dlp
- Deno

並依照：

```text
scripts/tools_manifest.json
```

中的 SHA-256 進行驗證。

驗證失敗時，檔案不會被採用。

---

# 🏗️ 建置 Windows 版本

建立 PyInstaller onedir 版本：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

若要同時建立正式 Installer：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build.ps1 -BuildInstaller
```

建立 Installer 需要：

```text
Inno Setup 6
```

---

# 🤖 GitHub Actions

專案已包含自動 Release Workflow。

每次正式版本 tag，例如：

```text
v2.7.0
```

推送到 GitHub 後，GitHub Actions 會自動執行：

```text
Checkout
↓
Python 環境
↓
單元測試
↓
PowerShell ASCII / Syntax 驗證
↓
下載固定版本工具
↓
SHA-256 驗證
↓
PyInstaller Build
↓
Inno Setup Installer
↓
Portable ZIP
↓
SHA256SUMS
↓
GitHub Release
```

正式 Release 僅會在：

```text
v*
```

tag 上建立。

手動執行 workflow 只會產生測試 Artifact，不會自動建立正式 Release。

---

# 📄 第三方元件與授權

本工具隨附或整合以下第三方開源元件：

### FFmpeg / ffprobe

- Version：9.0.1 Essentials Build
- Binary Build：Gyan.dev
- License：GPL-3.0

目前隨附的 Gyan.dev Essentials Build 使用 GPL 功能，因此實際隨附 binary 依 GPL-3.0 條款提供。

---

### yt-dlp

- Version：2026.08.19
- License：The Unlicense

---

### Deno

- Version：2.9.6
- License：MIT License

---

### Python / Tcl / Tk

- Python：PSF License
- Tcl / Tk：各自對應的開源授權條款

---

完整授權資訊、來源與相關說明請參閱：

**[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)**

---

# ⚖️ 使用聲明

本工具僅供使用者處理其：

- 有合法存取權限
- 可合法下載或處理
- 符合來源網站使用條款

的內容。

本程式本身不提供、也不以繞過下列機制為目的：

- DRM 數位版權管理
- 付費牆
- 會員權限限制
- 帳號登入驗證
- 私有內容存取控制

使用者應自行確認下載、保存或轉換內容是否符合所在地法律、著作權規定及來源網站的服務條款。

---

# 🐛 問題回報

如果遇到問題，請至：

**[GitHub Issues](https://github.com/nanachi1212/video-screenshot-extractor/issues)**

建議附上：

- Windows 版本
- 程式版本
- 錯誤訊息
- 問題發生步驟

請勿在 Issue 中公開：

- 密碼
- Cookie
- Token
- API Key
- 私人帳號資訊

---

# 📜 License

本專案本身採用：

**MIT License**

第三方執行元件仍分別遵循各自的授權條款。

詳細資訊請參閱：

**[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)**

---

## Video Screenshot Extractor

Windows GUI tool for downloading accessible public videos, extracting scene-change screenshots, and optionally exporting PNG, ZIP, MP4 and MP3 outputs.

**Latest Release：**

https://github.com/nanachi1212/video-screenshot-extractor/releases/latest
