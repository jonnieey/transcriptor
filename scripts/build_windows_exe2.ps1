# build_windows_exe.ps1
$ErrorActionPreference = "Stop"

# ----- 1. Check/Install GTK3 Runtime -----
$gtk3_install_path = "C:\Program Files\GTK3-Runtime Win64"
$local_gtk3_path = "$PSScriptRoot\gtk3"
$local_gtk3_path = [System.IO.Path]::GetFullPath($local_gtk3_path)

if (Test-Path $gtk3_install_path) {
    Write-Host "Found installed GTK3 runtime at $gtk3_install_path"
    Write-Host "Copying GTK3 runtime to local directory for bundling..."
    if (Test-Path $local_gtk3_path) { Remove-Item -Path $local_gtk3_path -Recurse -Force }
    Copy-Item -Path $gtk3_install_path -Destination $local_gtk3_path -Recurse -Force
} elseif (Test-Path $local_gtk3_path) {
    Write-Host "Using existing local 'gtk3' directory found at $local_gtk3_path"
} else {
    Write-Host "GTK3 runtime not found locally or in Program Files. Downloading installer..."
    $gtk3_url = "https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/download/2022-01-04/gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe"
    $installer_path = "$PSScriptRoot\gtk3-installer.exe"
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $gtk3_url -OutFile $installer_path
        Write-Host "Extracting GTK3 runtime to $local_gtk3_path..."
        $argList = "/S", "/D=$local_gtk3_path"
        $process = Start-Process -FilePath $installer_path -ArgumentList $argList -Wait -PassThru
        if ($process.ExitCode -ne 0) { throw "Installer exited with code $($process.ExitCode)" }
        if (-not (Test-Path "$local_gtk3_path\bin\libgtk-3-0.dll")) { throw "Extraction failed." }
        Write-Host "GTK3 runtime extracted successfully."
    } catch {
        Write-Host "Error downloading or extracting GTK3: $_"
        exit 1
    } finally {
        if (Test-Path $installer_path) { Remove-Item $installer_path }
    }
}

# ----- 2. Install uv and create a clean build environment -----
if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv..."
    python -m pip install uv
}

# $venv_dir = "$PSScriptRoot\.venv"
# Write-Host "Creating virtual environment with uv..."
# python -m uv venv $venv_dir --python 3.11   # or your preferred Python version

# Activate the virtual environment (in this script we'll use uv run)
# $venv_python = "$venv_dir\Scripts\python.exe"

# Install the project and its dependencies
Write-Host "Installing project in the virtual environment..."
python -m uv tool install -e .

# ----- 3. Generate a comprehensive spec file -----
$spec_content = @"
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=['$PSScriptRoot'],
    binaries=[],
    datas=[
        ('gtk3', 'gtk3'),               # Bundle the entire GTK3 folder
        ('tui.css', '.'),                # TUI stylesheet
    ],
    hiddenimports=[
        # Standard library hidden imports
        'encodings',
        # Third-party libraries
        'cmd2',
        'textual',
        'weasyprint',
        'cairosvg',
        'cffi',
        'prompt_toolkit',
        'sqlalchemy',
        'dateutil',
        'docx',
        'openpyxl',
        'pandas',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],                 # exclude if not used
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='transcriptor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,                         # keep console for TUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)
"@

$spec_file = "$PSScriptRoot\transcriptor.spec"
Set-Content -Path $spec_file -Value $spec_content -Encoding UTF8

# ----- 4. Build with PyInstaller (using the venv) -----
Write-Host "Installing PyInstaller in the virtual environment..."
python -m uv pip install pyinstaller

Write-Host "Building executable with PyInstaller..."
python -m uv run PyInstaller transcriptor.spec --clean --noconfirm

# ----- 5. Create Windows Terminal launcher -----
$dist_exe = "dist\transcriptor.exe"
if (Test-Path $dist_exe) {
    $launcher_path = "dist\transcriptor_wt.cmd"
    @"
@echo off
start "" wt.exe -d "%~dp0" transcriptor.exe
"@ | Out-File -FilePath $launcher_path -Encoding ascii
    Write-Host "Windows Terminal launcher created at $launcher_path"
    Write-Host "Build successful! Double-click transcriptor_wt.cmd to run in Windows Terminal."
} else {
    Write-Host "Build failed."
    exit 1
}
