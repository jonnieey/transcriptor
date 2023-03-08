import platform
import subprocess

from setuptools import setup

# Check if platform is Windows
if platform.system() == "Windows":
    # Check if GTK3 is installed
    try:
        print("Check if GTK3 is installed")
        subprocess.check_call(
            ["gtk3-demo", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("GTK3 is already installed")
    except:
        # Check if curl is installed
        try:
            subprocess.check_call(
                ["curl", "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except:
            # Install curl using Chocolatey
            print("Installing curl...")

            subprocess.check_call(
                [
                    "powershell",
                    "-Command",
                    "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))",
                ]
            )
            subprocess.check_call(["choco", "install", "curl", "-y"])

        print("Installing GTK3 runtime environment...")

        subprocess.check_call(
            [
                "curl",
                "-L",
                "-o",
                "gtk3-runtime.exe",
                "https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/download/2022-02-23/gtk3-runtime-3.24.30-2022-02-23-ts-win64.exe",
            ]
        )

        # Install GTK3 runtime environment and WeasyPrint
        subprocess.check_call(
            [
                ".gtk3-runtime.exe",
                "--no-desktop-file-install",
                "--no-menu-file-install",
                "--no-registry-file-install",
                "--no-themes",
            ]
        )

setup(name="transcriptor")
