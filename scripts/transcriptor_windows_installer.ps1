<#
.SYNOPSIS
    Downloads, builds, and installs Transcriptor on Windows.
.DESCRIPTION
    This script downloads the Transcriptor source code from GitHub,
    extracts it, and runs the build script to create the application
    and desktop shortcut.
.NOTES
    Run this script by right-clicking and selecting "Run with PowerShell".
    If PowerShell blocks execution, open a Command Prompt and run:
        powershell -ExecutionPolicy Bypass -File install_transcriptor.ps1
#>

$ErrorActionPreference = "Stop"

# ----- Configuration -----
$repoUrl = "https://github.com/jonnieey/transcriptor/archive/refs/heads/main.zip"
$tempDir = Join-Path $env:TEMP "transcriptor_install"
$zipPath = Join-Path $tempDir "source.zip"

Write-Host "Transcriptor Installer"
Write-Host "======================"

# ----- Clean and create temp folder -----
if (Test-Path $tempDir) {
    Remove-Item -Path $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# ----- Download source -----
Write-Host "Downloading Transcriptor source..."
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $repoUrl -OutFile $zipPath
} catch {
    Write-Host "Download failed: $_"
    exit 1
}

# ----- Extract -----
Write-Host "Extracting..."
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
$rootFolder = $zip.Entries[0].FullName.Split('/')[0]
[System.IO.Compression.ZipFile]::ExtractToDirectory($zipPath, $tempDir)
$zip.Dispose()

$sourceDir = Join-Path $tempDir $rootFolder
Write-Host "Source extracted to $sourceDir"

# ----- Run the build script -----
Write-Host "Running build script (this may take several minutes)..."
Push-Location $sourceDir
try {
    & ".\scripts\build_windows_exe.ps1"
    if ($LASTEXITCODE -ne 0) {
        throw "Build script failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}

# ----- Clean up (optional) -----
Write-Host "Cleaning up temporary files..."
Remove-Item -Path $tempDir -Recurse -Force

Write-Host "`nInstallation complete!"
Write-Host "Look for the 'Transcriptor' shortcut on your desktop."
Write-Host "If the shortcut is missing, check the build output above."
