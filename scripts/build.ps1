<#
.SYNOPSIS
    Builds VideoScreenshotExtractor onedir package and optional Inno Setup installer.
.PARAMETER SkipTests
    Skip running unit tests before build.
.PARAMETER BuildInstaller
    Compile Inno Setup installer if ISCC is found.
#>
param(
    [switch]$SkipTests,
    [switch]$BuildInstaller
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Get-Item "$PSScriptRoot\..").FullName
Set-Location $RepoRoot

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Building Video Screenshot Extractor v2.7.0" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Run Tests
if (-not $SkipTests) {
    Write-Host "[1/5] Running unit tests..." -ForegroundColor Yellow
    python -m unittest -v test_gui_core.GuiCoreTests
    if ($LASTEXITCODE -ne 0) {
        throw "Unit tests failed! Build aborted."
    }
    Write-Host "✓ All unit tests passed." -ForegroundColor Green
} else {
    Write-Host "[1/5] Skipping unit tests." -ForegroundColor DarkGray
}

# 2. Check and fetch tools
Write-Host "[2/5] Checking bundled runtime tools..." -ForegroundColor Yellow
$toolsDir = Join-Path $RepoRoot "tools"
$requiredTools = @("ffmpeg.exe", "ffprobe.exe", "yt-dlp.exe", "deno.exe")
$missing = $false
foreach ($t in $requiredTools) {
    if (-not (Test-Path (Join-Path $toolsDir $t))) {
        $missing = $true
        break
    }
}
if ($missing) {
    Write-Host "Tools missing in $toolsDir, calling fetch-tools.ps1..." -ForegroundColor Yellow
    & "$PSScriptRoot\fetch-tools.ps1"
} else {
    Write-Host "✓ All bundled tools present in $toolsDir." -ForegroundColor Green
}

# 3. Run PyInstaller
Write-Host "[3/5] Building with PyInstaller (onedir + windowed)..." -ForegroundColor Yellow
if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    throw "PyInstaller is not installed in current Python environment. Run 'pip install pyinstaller'."
}

pyinstaller VideoScreenshotExtractor.spec --clean --noconfirm
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed!"
}

# 4. Copy tools folder into dist
Write-Host "[4/5] Syncing tools folder to dist..." -ForegroundColor Yellow
$distAppDir = Join-Path $RepoRoot "dist\VideoScreenshotExtractor"
$distToolsDir = Join-Path $distAppDir "tools"
if (-not (Test-Path $distToolsDir)) {
    New-Item -ItemType Directory -Path $distToolsDir -Force | Out-Null
}
foreach ($t in $requiredTools) {
    Copy-Item -Path (Join-Path $toolsDir $t) -Destination (Join-Path $distToolsDir $t) -Force
}
Write-Host "✓ Bundled tools successfully copied to $distToolsDir" -ForegroundColor Green

# Verify output
$mainExe = Join-Path $distAppDir "VideoScreenshotExtractor.exe"
if (-not (Test-Path $mainExe)) {
    throw "Expected build artifact $mainExe not found!"
}
Write-Host "✓ Onedir application build verified at: $distAppDir" -ForegroundColor Green

# 5. Inno Setup Build (Optional / Automatic if available)
Write-Host "[5/5] Checking Inno Setup compiler..." -ForegroundColor Yellow
$isccCandidates = @(
    "ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
)
$isccPath = $null
foreach ($cand in $isccCandidates) {
    if (Get-Command $cand -ErrorAction SilentlyContinue) {
        $isccPath = (Get-Command $cand).Source
        break
    }
    if (Test-Path $cand) {
        $isccPath = $cand
        break
    }
}

$releaseDir = Join-Path $RepoRoot "release"
New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null

if ($isccPath) {
    Write-Host "Compiling installer using $isccPath..." -ForegroundColor Cyan
    $issFile = Join-Path $RepoRoot "installer\VideoScreenshotExtractor.iss"
    & "$isccPath" "$issFile"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Installer build succeeded in $releaseDir" -ForegroundColor Green
    } else {
        Write-Warning "Inno Setup compilation returned non-zero exit code: $LASTEXITCODE"
    }
} else {
    Write-Host "Inno Setup (ISCC.exe) not found on this system." -ForegroundColor Yellow
    Write-Host "Onedir package is ready. To build the installer, install Inno Setup 6 or run via GitHub Actions." -ForegroundColor Yellow
}

# Checksum report
Write-Host "`nArtifacts and Checksums:" -ForegroundColor Cyan
Get-ChildItem -Path $releaseDir -Filter "*.exe" -ErrorAction SilentlyContinue | ForEach-Object {
    $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
    Write-Host "$($_.Name) (SHA-256: $hash)" -ForegroundColor Green
}
