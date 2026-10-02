<#
.SYNOPSIS
    Small local CI dispatcher for VideoScreenshotExtractor.

.DESCRIPTION
    Auto selects the lowest useful validation from deterministic changed paths.
    Full and Live are explicit because they build or execute external tools.
#>
param(
    [ValidateSet('Auto', 'Fast', 'Full', 'Live')]
    [string]$Mode = 'Auto',
    [string[]]$ChangedPath = @(),
    [switch]$PlanOnly
)

$ErrorActionPreference = 'Stop'
$RepoRoot = (Get-Item (Join-Path $PSScriptRoot '..')).FullName
Set-Location $RepoRoot

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$File,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    & $File @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$File exited with code $LASTEXITCODE"
    }
}

function Get-ChangedPaths {
    if ($ChangedPath.Count -gt 0) {
        return @($ChangedPath | ForEach-Object { $_ -replace '\\', '/' })
    }

    $paths = @()
    $paths += @(git diff --name-only origin/main...HEAD 2>$null)
    $paths += @(git diff --name-only)
    $paths += @(git ls-files --others --exclude-standard)
    return @($paths | Where-Object { $_ } | Sort-Object -Unique | ForEach-Object { $_ -replace '\\', '/' })
}

function Test-PowerShellSyntax {
    $files = @(Get-ChildItem (Join-Path $RepoRoot 'scripts') -Filter '*.ps1' -File -ErrorAction SilentlyContinue)
    foreach ($file in $files) {
        $tokens = $null
        $errors = $null
        [System.Management.Automation.Language.Parser]::ParseFile(
            $file.FullName,
            [ref]$tokens,
            [ref]$errors
        ) | Out-Null
        if ($errors.Count -gt 0) {
            throw "PowerShell parse failed: $($file.FullName): $($errors[0].Message)"
        }
    }
    Write-Host ('PowerShell syntax: PASS ({0} scripts)' -f $files.Count)
}

function Get-Actions {
    param([string[]]$Paths)

    $unit = $false
    $powershell = $false
    foreach ($path in $Paths) {
        if ($path -match '^(app\.py|gui_core\.py|test_gui_core\.py|version\.py|VERSION|requirements(?:-.*)?\.txt|VideoScreenshotExtractor\.spec)$') {
            $unit = $true
        }
        if ($path -match '^scripts/.*\.ps1$') {
            $powershell = $true
        }
    }
    return [pscustomobject]@{ Unit = $unit; PowerShell = $powershell }
}

function Show-Plan {
    param([string]$SelectedMode, [string[]]$Paths, $Actions)

    Write-Host "Mode: $SelectedMode"
    Write-Host ('Changed paths: {0}' -f ($(if ($Paths.Count) { $Paths -join ', ' } else { '(none)' })))
    if ($SelectedMode -eq 'Fast') { Write-Host 'Plan: unit tests' }
    elseif ($SelectedMode -eq 'Full') { Write-Host 'Plan: unit tests, PowerShell syntax, package build' }
    elseif ($SelectedMode -eq 'Live') { Write-Host 'Plan: packaged runtime smoke' }
    elseif (-not ($Actions.Unit -or $Actions.PowerShell)) { Write-Host 'WARN / NOT_TESTED: no affected validation target' }
    else {
        if ($Actions.Unit) { Write-Host 'Plan: unit tests' }
        if ($Actions.PowerShell) { Write-Host 'Plan: PowerShell syntax' }
    }
}

$paths = @(Get-ChangedPaths)
$actions = Get-Actions -Paths $paths
Show-Plan -SelectedMode $Mode -Paths $paths -Actions $actions
if ($PlanOnly) { exit 0 }

switch ($Mode) {
    'Fast' {
        Invoke-Checked -File 'python' -Arguments @('-m', 'unittest', '-v', 'test_gui_core.GuiCoreTests')
    }
    'Full' {
        Invoke-Checked -File 'python' -Arguments @('-m', 'unittest', '-v', 'test_gui_core.GuiCoreTests')
        Test-PowerShellSyntax
        Invoke-Checked -File 'powershell.exe' -Arguments @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $PSScriptRoot 'build.ps1'), '-SkipTests')
    }
    'Live' {
        $dist = Join-Path $RepoRoot 'dist\VideoScreenshotExtractor'
        if (-not (Test-Path (Join-Path $dist 'VideoScreenshotExtractor.exe'))) {
            throw 'Live smoke requires a packaged dist\VideoScreenshotExtractor build.'
        }
        Invoke-Checked -File 'powershell.exe' -Arguments @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $PSScriptRoot 'smoke_test.ps1'))
    }
    'Auto' {
        if (-not ($actions.Unit -or $actions.PowerShell)) {
            Write-Host 'WARN / NOT_TESTED: unrelated paths only'
            break
        }
        if ($actions.Unit) {
            Invoke-Checked -File 'python' -Arguments @('-m', 'unittest', '-v', 'test_gui_core.GuiCoreTests')
        }
        if ($actions.PowerShell) {
            Test-PowerShellSyntax
        }
    }
}

Write-Host 'Local CI: PASS'
