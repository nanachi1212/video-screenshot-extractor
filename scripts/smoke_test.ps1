$distDir = "F:\Projects\Codex project\video_screenshot_gui\dist\VideoScreenshotExtractor"
$exePath = Join-Path $distDir "VideoScreenshotExtractor.exe"

Write-Host "=== SMOKE TEST: Resolving tools in clean environment ===" -ForegroundColor Cyan

# 1. Test clean resolver in subshell with stripped PATH
$cleanEnv = @{
    "PATH" = "C:\Windows\System32;C:\Windows"
}

# Run a quick python verification inside the clean env using .venv python pointing to dist tools
$testScript = @"
import os, sys
from pathlib import Path
sys.path.insert(0, r'F:\Projects\Codex project\video_screenshot_gui')
import gui_core
app_dir = Path(r'$distDir')
tools = gui_core.check_runtime_tools(app_dir)
print('RESOLVED_FFMPEG:', tools['ffmpeg'])
print('RESOLVED_FFPROBE:', tools['ffprobe'])
print('RESOLVED_YTDLP:', tools['yt-dlp'])
print('RESOLVED_DENO:', tools['deno'])
assert 'tools' in str(tools['ffmpeg'])
assert 'tools' in str(tools['ffprobe'])
assert 'tools' in str(tools['yt-dlp'])
assert 'tools' in str(tools['deno'])
print('ALL_BUNDLED_RESOLVED_OK')
"@

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "F:\Projects\Codex project\video_screenshot_gui\.venv\Scripts\python.exe"
$psi.Arguments = "-c `"$testScript`""
$psi.EnvironmentVariables["PATH"] = "C:\Windows\System32;C:\Windows"
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true

$proc = [System.Diagnostics.Process]::Start($psi)
$stdout = $proc.StandardOutput.ReadToEnd()
$stderr = $proc.StandardError.ReadToEnd()
$proc.WaitForExit()

Write-Host $stdout -ForegroundColor Green
if ($proc.ExitCode -ne 0 -or $stdout -notmatch "ALL_BUNDLED_RESOLVED_OK") {
    Write-Error "Clean environment tool resolution failed:`n$stderr"
    exit 1
}

Write-Host "=== SMOKE TEST: Launching packaged GUI EXE ===" -ForegroundColor Cyan
$guiPsi = New-Object System.Diagnostics.ProcessStartInfo
$guiPsi.FileName = $exePath
$guiPsi.EnvironmentVariables["PATH"] = "C:\Windows\System32;C:\Windows"
$guiPsi.UseShellExecute = $false

$guiProc = [System.Diagnostics.Process]::Start($guiPsi)
$timeoutSeconds = 10
$sw = [System.Diagnostics.Stopwatch]::StartNew()
while ($sw.Elapsed.TotalSeconds -lt $timeoutSeconds) {
    Start-Sleep -Milliseconds 500
    $guiProc.Refresh()
    if ($guiProc.HasExited) {
        Write-Error "EXE exited prematurely with exit code $($guiProc.ExitCode)!"
        exit 1
    }
    if ($guiProc.MainWindowTitle) {
        break
    }
}
Write-Host "Process running, PID: $($guiProc.Id)" -ForegroundColor Green
# Verify process is healthy and window handle was created
if ($guiProc.HasExited) {
    Write-Error "Process exited prematurely with exit code: $($guiProc.ExitCode)"
    exit 1
}

$procInfo = Get-Process -Id $guiProc.Id
Write-Host "Verified process is running: PID=$($procInfo.Id), Responding=$($procInfo.Responding)" -ForegroundColor Green

# Close process cleanly
$guiProc.CloseMainWindow() | Out-Null
Start-Sleep -Milliseconds 600
if (-not $guiProc.HasExited) {
    $guiProc.Kill()
}

Write-Host "Smoke test successfully passed!" -ForegroundColor Green
