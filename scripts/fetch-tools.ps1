<#
.SYNOPSIS
    Downloads and verifies pinned runtime binaries (ffmpeg, ffprobe, yt-dlp, deno) for Windows packaging.
.PARAMETER TargetDir
    Target directory where executables will be placed (default: <repo_root>/tools).
.PARAMETER Force
    Force re-download even if binaries already exist.
.PARAMETER UseLocalInstalled
    If set, copies existing binaries from current Windows environment instead of downloading.
#>
param(
    [string]$TargetDir = "$PSScriptRoot\..\tools",
    [switch]$Force,
    [switch]$UseLocalInstalled
)

$ErrorActionPreference = "Stop"

$ResolvedTargetDir = (New-Item -ItemType Directory -Path $TargetDir -Force).FullName
Write-Host "Target tools directory: $ResolvedTargetDir" -ForegroundColor Cyan

$Tools = @{
    "ffmpeg.exe"  = $false
    "ffprobe.exe" = $false
    "yt-dlp.exe"  = $false
    "deno.exe"    = $false
}

# Check if all exist
$AllExist = $true
foreach ($tool in $Tools.Keys) {
    $dest = Join-Path $ResolvedTargetDir $tool
    if (Test-Path $dest) {
        $Tools[$tool] = $true
    } else {
        $AllExist = $false
    }
}

if ($AllExist -and -not $Force) {
    Write-Host "All tools already exist in $ResolvedTargetDir. Use -Force to re-download." -ForegroundColor Green
    return
}

# Option: Copy from locally installed winget / system path if requested
if ($UseLocalInstalled) {
    Write-Host "Copying tools from local environment..." -ForegroundColor Yellow
    $LocalCommands = @{
        "ffmpeg.exe"  = (Get-Command ffmpeg.exe -ErrorAction SilentlyContinue)
        "ffprobe.exe" = (Get-Command ffprobe.exe -ErrorAction SilentlyContinue)
        "yt-dlp.exe"  = (Get-Command yt-dlp.exe -ErrorAction SilentlyContinue)
        "deno.exe"    = (Get-Command deno.exe -ErrorAction SilentlyContinue)
    }

    $allFound = $true
    foreach ($k in $LocalCommands.Keys) {
        $cmd = $LocalCommands[$k]
        if ($cmd) {
            Copy-Item -Path $cmd.Source -Destination (Join-Path $ResolvedTargetDir $k) -Force
            Write-Host "Copied $k from $($cmd.Source)" -ForegroundColor Green
        } else {
            Write-Warning "Local command for $k not found."
            $allFound = $false
        }
    }
    if ($allFound) {
        Write-Host "All tools populated from local environment." -ForegroundColor Green
        return
    }
    Write-Host "Falling back to downloading official pinned binaries..." -ForegroundColor Yellow
}

$TempDir = Join-Path ([System.IO.Path]::GetTempPath()) "vse_tool_downloads"
$null = New-Item -ItemType Directory -Path $TempDir -Force

# Pinned official URLs
$YtDlpUrl = "https://github.com/yt-dlp/yt-dlp/releases/download/2025.02.19/yt-dlp.exe"
$DenoUrl   = "https://github.com/denoland/deno/releases/download/v2.2.3/deno-x86_64-pc-windows-msvc.zip"
$FFmpegUrl = "https://github.com/GyanD/codexffmpeg/releases/download/7.1/ffmpeg-7.1-essentials_build.zip"

try {
    # 1. yt-dlp.exe
    $ytDlpDest = Join-Path $ResolvedTargetDir "yt-dlp.exe"
    if (-not (Test-Path $ytDlpDest) -or $Force) {
        Write-Host "Downloading yt-dlp.exe (2025.02.19)..." -ForegroundColor Cyan
        Invoke-WebRequest -Uri $YtDlpUrl -OutFile $ytDlpDest -UseBasicParsing
        Write-Host "✓ yt-dlp.exe downloaded." -ForegroundColor Green
    }

    # 2. deno.exe
    $denoDest = Join-Path $ResolvedTargetDir "deno.exe"
    if (-not (Test-Path $denoDest) -or $Force) {
        Write-Host "Downloading Deno (v2.2.3)..." -ForegroundColor Cyan
        $denoZip = Join-Path $TempDir "deno.zip"
        Invoke-WebRequest -Uri $DenoUrl -OutFile $denoZip -UseBasicParsing
        $denoExtract = Join-Path $TempDir "deno_extracted"
        Expand-Archive -Path $denoZip -DestinationPath $denoExtract -Force
        $denoExe = Get-ChildItem -Path $denoExtract -Filter "deno.exe" -Recurse | Select-Object -First 1
        if ($denoExe) {
            Copy-Item -Path $denoExe.FullName -Destination $denoDest -Force
            Write-Host "✓ deno.exe extracted." -ForegroundColor Green
        } else {
            throw "Failed to find deno.exe in extracted archive."
        }
    }

    # 3. ffmpeg.exe & ffprobe.exe
    $ffmpegDest = Join-Path $ResolvedTargetDir "ffmpeg.exe"
    $ffprobeDest = Join-Path $ResolvedTargetDir "ffprobe.exe"
    if (-not (Test-Path $ffmpegDest) -or -not (Test-Path $ffprobeDest) -or $Force) {
        Write-Host "Downloading FFmpeg (7.1 essentials)..." -ForegroundColor Cyan
        $ffmpegZip = Join-Path $TempDir "ffmpeg.zip"
        Invoke-WebRequest -Uri $FFmpegUrl -OutFile $ffmpegZip -UseBasicParsing
        $ffmpegExtract = Join-Path $TempDir "ffmpeg_extracted"
        Expand-Archive -Path $ffmpegZip -DestinationPath $ffmpegExtract -Force
        $ffExe = Get-ChildItem -Path $ffmpegExtract -Filter "ffmpeg.exe" -Recurse | Select-Object -First 1
        $probeExe = Get-ChildItem -Path $ffmpegExtract -Filter "ffprobe.exe" -Recurse | Select-Object -First 1
        if ($ffExe -and $probeExe) {
            Copy-Item -Path $ffExe.FullName -Destination $ffmpegDest -Force
            Copy-Item -Path $probeExe.FullName -Destination $ffprobeDest -Force
            Write-Host "✓ ffmpeg.exe and ffprobe.exe extracted." -ForegroundColor Green
        } else {
            throw "Failed to find ffmpeg.exe or ffprobe.exe in extracted archive."
        }
    }

    Write-Host "All tools successfully provisioned to $ResolvedTargetDir" -ForegroundColor Green
}
finally {
    Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
}
