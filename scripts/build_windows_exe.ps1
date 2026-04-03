# build_windows_exe.ps1
$ErrorActionPreference = "Stop"

# ----- 1. Install uv if not present -----
if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/0.10.4/install.ps1 | iex"
    # Refresh PATH so uv becomes available immediately
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# ----- 2. Install Python 3.11 via uv (if not already available) -----
Write-Host "Ensuring Python 3.11 is available via uv..."
uv python install 3.11

# ----- 3. PDF Backend Selection -----
Write-Host "`n=== PDF Backend Selection ==="
Write-Host "Transcriptor supports multiple PDF rendering engines for invoice generation."
Write-Host "Choose a backend (default is Playwright):"
Write-Host "1. Playwright - Recommended for Windows, uses headless Chromium"
Write-Host "2. xhtml2pdf - Pure Python, limited CSS support"
Write-Host "3. WeasyPrint - Requires GTK3 runtime libraries"
Write-Host "4. All backends - Install all three (larger package)"
Write-Host ""

$backendChoice = Read-Host "Enter choice [1-4] (default: 1)"
if ([string]::IsNullOrWhiteSpace($backendChoice)) { $backendChoice = "1" }

switch ($backendChoice) {
    "1" {
        $backendName = "playwright"
        $backendExtra = "[playwright]"
        Write-Host "Selected: Playwright backend"
    }
    "2" {
        $backendName = "xhtml2pdf"
        $backendExtra = "[xhtml2pdf]"
        Write-Host "Selected: xhtml2pdf backend"
    }
    "3" {
        $backendName = "weasyprint"
        $backendExtra = "[weasyprint]"
        Write-Host "Selected: WeasyPrint backend"
    }
    "4" {
        $backendName = "all"
        $backendExtra = "[all]"
        Write-Host "Selected: All backends"
    }
    default {
        $backendName = "playwright"
        $backendExtra = "[playwright]"
        Write-Host "Invalid choice, defaulting to Playwright"
    }
}

# ----- 4. GTK3 runtime handling (only for WeasyPrint or all backends) -----
if ($backendName -eq "weasyprint" -or $backendName -eq "all") {
    Write-Host "`n=== GTK3 Runtime Setup (Required for WeasyPrint) ==="
    $gtk3_install_path = "C:\Program Files\GTK3-Runtime Win64"
    $local_gtk3_path = "$PSScriptRoot\..\gtk3"
    $local_gtk3_path = [System.IO.Path]::GetFullPath($local_gtk3_path)

    if (Test-Path $gtk3_install_path) {
        Write-Host "Found installed GTK3 runtime at $gtk3_install_path"
        Write-Host "Copying GTK3 runtime to local directory for bundling..."
        if (Test-Path $local_gtk3_path) { Remove-Item -Path $local_gtk3_path -Recurse -Force }
        Copy-Item -Path $gtk3_install_path -Destination $local_gtk3_path -Recurse -Force
    } elseif (Test-Path $local_gtk3_path) {
        Write-Host "Using existing local 'gtk3' directory found at $local_gtk3_path"
    } else {
        Write-Host "GTK3 runtime not found locally or in Program Files."
        Write-Host "Downloading GTK3 runtime installer..."

        $gtk3_url = "https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/download/2022-01-04/gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe"
        $installer_path = "$PSScriptRoot\gtk3-installer.exe"

        try {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -Uri $gtk3_url -OutFile $installer_path

            Write-Host "Extracting GTK3 runtime to $local_gtk3_path..."
            $argList = "/S", "/D=$local_gtk3_path"
            $process = Start-Process -FilePath $installer_path -ArgumentList $argList -Wait -PassThru

            if ($process.ExitCode -ne 0) {
                throw "Installer exited with code $($process.ExitCode)"
            }

            if (-not (Test-Path "$local_gtk3_path\bin\libgtk-3-0.dll")) {
                throw "Extraction failed. The DLLs are missing."
            }

            Write-Host "GTK3 runtime extracted successfully."
        } catch {
            Write-Host "Error downloading or extracting GTK3: $_"
            Write-Host "WeasyPrint backend will not work without GTK3 runtime."
            exit 1
        } finally {
            if (Test-Path $installer_path) { Remove-Item $installer_path }
        }
    }
} else {
    Write-Host "`n=== Skipping GTK3 (not needed for $backendName backend) ==="
}

# ----- 4. Install the tool using uv tool install (with Python 3.11) -----
Write-Host "Installing 'trans5' tool via uv (Python 3.11) with $backendName backend..."
uv tool install --python 3.11 --force ".$backendExtra"

# For Playwright backend, install browser binaries
if ($backendName -eq "playwright" -or $backendName -eq "all") {
    Write-Host "Installing Playwright browser binaries..."
    & uv run playwright install
}

# Locate trans5.exe – it should be in %USERPROFILE%\.local\bin
$trans5_exe = "$env:USERPROFILE\.local\bin\trans5.exe"
if (-not (Test-Path $trans5_exe)) {
    Write-Host "Error: trans5.exe not found at expected location: $trans5_exe"
    exit 1
}
Write-Host "Found trans5.exe at $trans5_exe"

# ----- 5. Create a temporary virtual environment for building the launcher -----
$venv_dir = "$env:TEMP\transcriptor_launcher_venv"
if (Test-Path $venv_dir) { Remove-Item -Path $venv_dir -Recurse -Force }

Write-Host "Creating temporary virtual environment for launcher build..."
uv venv --python 3.11 $venv_dir

# ----- 6. Install PyInstaller -----
Write-Host "Installing PyInstaller in temporary environment..."
& uv pip install pyinstaller

# ----- 7. Create launcher Python script -----
$launcher_script_dir = "$env:TEMP\transcriptor_launcher_src"
if (Test-Path $launcher_script_dir) { Remove-Item -Path $launcher_script_dir -Recurse -Force }
New-Item -ItemType Directory -Path $launcher_script_dir -Force | Out-Null

$launcher_script = @"
import subprocess
import sys
import os
import shutil

def main():
    trans5_path = r"$trans5_exe"
    wt_path = shutil.which("wt.exe")
    if wt_path:
        try:
            # CREATE_NEW_CONSOLE = 0x00000010
            subprocess.Popen([wt_path, trans5_path], creationflags=0x00000010)
        except Exception:
            subprocess.Popen([trans5_path], creationflags=0x00000010)
    else:
        subprocess.Popen([trans5_path], creationflags=0x00000010)
    sys.exit(0)

if __name__ == "__main__":
    main()
"@

$launcher_script | Out-File -FilePath "$launcher_script_dir\launcher.py" -Encoding utf8

# ----- 8. Build launcher with PyInstaller (using the venv) -----
Write-Host "Building launcher executable as 'launch_transcriptor.exe'..."
& uv run pyinstaller --onefile --noconsole --name launch_transcriptor --distpath "$launcher_script_dir\dist" --workpath "$launcher_script_dir\build" --specpath "$launcher_script_dir" "$launcher_script_dir\launcher.py"

# ----- 9. Move launcher to %USERPROFILE%\.local\bin -----
$target_bin = "$env:USERPROFILE\.local\bin"
if (-not (Test-Path $target_bin)) {
    New-Item -ItemType Directory -Path $target_bin -Force | Out-Null
}
$launcher_exe = "$launcher_script_dir\dist\launch_transcriptor.exe"
$final_launcher = "$target_bin\launch_transcriptor.exe"
Move-Item -Path $launcher_exe -Destination $final_launcher -Force

# ----- 10. Create desktop shortcut -----
$desktop = [System.Environment]::GetFolderPath("Desktop")
$shortcut_path = "$desktop\Transcriptor.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcut_path)
$shortcut.TargetPath = $final_launcher
$shortcut.WorkingDirectory = $target_bin
$shortcut.Description = "Launch Transcriptor in Windows Terminal"
$shortcut.Save()

# ----- 11. Cleanup temporary folders -----
Remove-Item -Path $venv_dir -Recurse -Force
Remove-Item -Path $launcher_script_dir -Recurse -Force

# ----- 12. Report success -----
Write-Host "Build successful!"
Write-Host "Main application: $trans5_exe"
Write-Host "Launcher executable: $final_launcher"
Write-Host "Desktop shortcut created: $shortcut_path"
Write-Host "You can now double-click the desktop shortcut to run Transcriptor in Windows Terminal."
