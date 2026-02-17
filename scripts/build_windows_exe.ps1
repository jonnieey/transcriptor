# Windows Build Script
# This script is intended to be run on Windows to build the executable.

$ErrorActionPreference = "Stop"

# Ensure Python is installed
try {
    python --version
} catch {
    Write-Host "Python is not installed. Please install Python from python.org."
    exit 1
}

# Install PyInstaller if not present
try {
    python -m pip show pyinstaller
} catch {
    Write-Host "Installing PyInstaller..."
    python -m pip install pyinstaller
}

# Install project dependencies
try {
    if (Get-Command "uv" -ErrorAction SilentlyContinue) {
        Write-Host "Using uv to install dependencies..."
        uv pip install .
    } else {
        Write-Host "Using pip to install dependencies..."
        python -m pip install .
    }
} catch {
    Write-Host "Failed to install dependencies."
    exit 1
}

# Build the executable using PyInstaller
Write-Host "Building executable..."
pyinstaller transcriptor.spec --clean --noconfirm

if (Test-Path "dist\transcriptor.exe") {
    Write-Host "Build successful! The executable is located at dist\transcriptor.exe"

    # Optional: Suggest checking for GTK3 runtime for WeasyPrint
    Write-Host "Note: WeasyPrint requires GTK3 runtime libraries on Windows."
    Write-Host "Ensure the GTK3 runtime is installed on the target machine or its DLLs are bundled."
    Write-Host "Download GTK3 installer from: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases"
} else {
    Write-Host "Build failed."
    exit 1
}
