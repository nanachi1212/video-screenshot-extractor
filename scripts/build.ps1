<#
.SYNOPSIS
    Builds VideoScreenshotExtractor onedir package and optional Inno Setup installer.
.PARAMETER SkipTests
    Skip running unit tests before build.
.PARAMETER BuildInstaller
    Compile Inno Setup installer. Requires Inno Setup 6 (ISCC.exe).
#>
param(
    [switch]$SkipTests,
    [switch]$BuildInstaller
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Get-Item "$PSScriptRoot\..").FullName
Set-Location $RepoRoot

# Read central version source of truth
$VersionFile = Join-Path $RepoRoot "VERSION"
if (-not (Test-Path $VersionFile)) {
    throw "VERSION file not found at $VersionFile!"
}
$Version = (Get-Content $VersionFile -Raw).Trim()

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Building Video Screenshot Extractor v$Version" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Locate Python executable (prefer local .venv if available)
$pythonExe = "python"
$venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $pythonExe = $venvPython
    Write-Host "Using virtual environment Python: $pythonExe" -ForegroundColor Green
}

# 1. Run Tests
if (-not $SkipTests) {
    Write-Host "[1/5] Running unit tests..." -ForegroundColor Yellow
    & $pythonExe -m unittest -v test_gui_core.GuiCoreTests
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
    Write-Host "Tools missing in $toolsDir, invoking fetch-tools.ps1 with SHA-256 verification..." -ForegroundColor Yellow
    & "$PSScriptRoot\fetch-tools.ps1"
} else {
    Write-Host "✓ All bundled tools present in $toolsDir." -ForegroundColor Green
}

# 3. Locate and run PyInstaller
Write-Host "[3/5] Building with PyInstaller (onedir + windowed)..." -ForegroundColor Yellow
$pyinstallerCmd = $null
$venvPyinstaller = Join-Path $RepoRoot ".venv\Scripts\pyinstaller.exe"
if (Test-Path $venvPyinstaller) {
    $pyinstallerCmd = $venvPyinstaller
} elseif (Get-Command pyinstaller.exe -ErrorAction SilentlyContinue) {
    $pyinstallerCmd = (Get-Command pyinstaller.exe).Source
}

if (-not $pyinstallerCmd) {
    throw "PyInstaller was not found in .venv or PATH. Please install it with 'pip install pyinstaller'."
}

Write-Host "Invoking PyInstaller: $pyinstallerCmd" -ForegroundColor Cyan
& $pyinstallerCmd VideoScreenshotExtractor.spec --clean --noconfirm
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

# 5. Inno Setup Build (Only when -BuildInstaller is explicitly requested)
$releaseDir = Join-Path $RepoRoot "release"
New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null

if ($BuildInstaller) {
    Write-Host "[5/5] Building Inno Setup installer..." -ForegroundColor Yellow
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

    if (-not $isccPath) {
        throw "Inno Setup compiler (ISCC.exe) not found on this system! Please install Inno Setup 6 or run in CI."
    }

    Write-Host "Compiling installer using $isccPath (Version: $Version)..." -ForegroundColor Cyan
    $issFile = Join-Path $RepoRoot "installer\VideoScreenshotExtractor.iss"
    & "$isccPath" "/DMyAppVersion=$Version" "$issFile"
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup compilation failed with exit code $LASTEXITCODE"
    }
    Write-Host "✓ Installer successfully created in $releaseDir" -ForegroundColor Green
} else {
    Write-Host "[5/5] Skipping installer compilation (-BuildInstaller switch not specified). Onedir package is ready." -ForegroundColor Yellow
}

# Checksum report for any release artifacts
$releaseArtifacts = Get-ChildItem -Path $releaseDir -Filter "*.exe" -ErrorAction SilentlyContinue
if ($releaseArtifacts) {
    Write-Host "`nRelease Artifacts and Checksums:" -ForegroundColor Cyan
    $releaseArtifacts | ForEach-Object {
        $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
        $sizeMB = [math]::Round($_.Length / 1MB, 2)
        Write-Host "$($_.Name) ($sizeMB MB) [SHA-256: $hash]" -ForegroundColor Green
    }
}
