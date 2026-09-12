<#
.SYNOPSIS
    Downloads and verifies pinned runtime binaries (ffmpeg, ffprobe, yt-dlp, deno)
    with strict SHA-256 verification against scripts/tools_manifest.json.
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

$ManifestPath = Join-Path $PSScriptRoot "tools_manifest.json"
if (-not (Test-Path $ManifestPath)) {
    throw "Manifest file not found at $ManifestPath!"
}

$Manifest = Get-Content $ManifestPath -Raw -Encoding utf8 | ConvertFrom-Json
$ResolvedTargetDir = (New-Item -ItemType Directory -Path $TargetDir -Force).FullName
Write-Host "Target tools directory: $ResolvedTargetDir" -ForegroundColor Cyan

# Check if all required files exist
$RequiredFiles = @("ffmpeg.exe", "ffprobe.exe", "yt-dlp.exe", "deno.exe")
$AllExist = $true
foreach ($f in $RequiredFiles) {
    if (-not (Test-Path (Join-Path $ResolvedTargetDir $f))) {
        $AllExist = $false
        break
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
            Write-Host "[OK] Copied $k from $($cmd.Source)" -ForegroundColor Green
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

$TempDir = Join-Path ([System.IO.Path]::GetTempPath()) "vse_tool_downloads_$(Get-Random)"
$null = New-Item -ItemType Directory -Path $TempDir -Force

function Verify-Sha256 {
    param(
        [string]$FilePath,
        [string]$ExpectedHash,
        [string]$ItemName
    )
    Write-Host "Verifying SHA-256 for $ItemName..." -ForegroundColor Cyan
    $ActualHash = (Get-FileHash -Path $FilePath -Algorithm SHA256).Hash.ToLowerInvariant()
    $ExpectedHashClean = $ExpectedHash.Trim().ToLowerInvariant()
    if ($ActualHash -ne $ExpectedHashClean) {
        Remove-Item -Path $FilePath -Force -ErrorAction SilentlyContinue
        throw "CRITICAL SECURITY FAILURE: SHA-256 hash mismatch for $ItemName!`nExpected: $ExpectedHashClean`nActual:   $ActualHash`nDownload was aborted and untrusted file was deleted."
    }
    Write-Host "[OK] SHA-256 verified for ${ItemName}: $ActualHash" -ForegroundColor Green
}

try {
    # 1. yt-dlp
    $ytTarget = Join-Path $ResolvedTargetDir "yt-dlp.exe"
    if (-not (Test-Path $ytTarget) -or $Force) {
        $ytInfo = $Manifest.'yt-dlp'
        $ytTemp = Join-Path $TempDir "yt-dlp.exe"
        Write-Host "Downloading yt-dlp ($($ytInfo.version))..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $ytInfo.url -OutFile $ytTemp -UseBasicParsing
        Verify-Sha256 -FilePath $ytTemp -ExpectedHash $ytInfo.sha256 -ItemName "yt-dlp.exe"
        Copy-Item -Path $ytTemp -Destination $ytTarget -Force
        Write-Host "[OK] Installed yt-dlp.exe" -ForegroundColor Green
    }

    # 2. Deno
    $denoTarget = Join-Path $ResolvedTargetDir "deno.exe"
    if (-not (Test-Path $denoTarget) -or $Force) {
        $denoInfo = $Manifest.'deno'
        $denoZip = Join-Path $TempDir "deno.zip"
        Write-Host "Downloading Deno ($($denoInfo.version))..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $denoInfo.url -OutFile $denoZip -UseBasicParsing
        Verify-Sha256 -FilePath $denoZip -ExpectedHash $denoInfo.sha256 -ItemName "Deno zip archive"
        $denoExtract = Join-Path $TempDir "deno_extracted"
        Expand-Archive -Path $denoZip -DestinationPath $denoExtract -Force
        $denoExe = Get-ChildItem -Path $denoExtract -Filter "deno.exe" -Recurse | Select-Object -First 1
        if (-not $denoExe) {
            throw "Failed to locate deno.exe inside extracted archive!"
        }
        Copy-Item -Path $denoExe.FullName -Destination $denoTarget -Force
        Write-Host "[OK] Installed deno.exe" -ForegroundColor Green
    }

    # 3. FFmpeg & FFprobe (Gyan Essentials)
    $ffmpegTarget = Join-Path $ResolvedTargetDir "ffmpeg.exe"
    $ffprobeTarget = Join-Path $ResolvedTargetDir "ffprobe.exe"
    if (-not (Test-Path $ffmpegTarget) -or -not (Test-Path $ffprobeTarget) -or $Force) {
        $ffInfo = $Manifest.'ffmpeg'
        $ffZip = Join-Path $TempDir "ffmpeg-essentials.zip"
        Write-Host "Downloading FFmpeg Essentials ($($ffInfo.version))..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $ffInfo.url -OutFile $ffZip -UseBasicParsing
        Verify-Sha256 -FilePath $ffZip -ExpectedHash $ffInfo.sha256 -ItemName "FFmpeg Essentials zip archive"
        $ffExtract = Join-Path $TempDir "ffmpeg_extracted"
        Expand-Archive -Path $ffZip -DestinationPath $ffExtract -Force
        $ffExe = Get-ChildItem -Path $ffExtract -Filter "ffmpeg.exe" -Recurse | Select-Object -First 1
        $probeExe = Get-ChildItem -Path $ffExtract -Filter "ffprobe.exe" -Recurse | Select-Object -First 1
        if (-not $ffExe -or -not $probeExe) {
            throw "Failed to locate ffmpeg.exe or ffprobe.exe in extracted archive!"
        }
        Copy-Item -Path $ffExe.FullName -Destination $ffmpegTarget -Force
        Copy-Item -Path $probeExe.FullName -Destination $ffprobeTarget -Force
        Write-Host "[OK] Installed ffmpeg.exe and ffprobe.exe" -ForegroundColor Green
    }

    Write-Host "All bundled tools successfully fetched and verified." -ForegroundColor Green
}
finally {
    Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
}
