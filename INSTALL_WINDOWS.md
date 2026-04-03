# Installation Instructions for Windows

For Windows users who are not comfortable with command-line tools or installing Python manually, the recommended approach is to download the standalone executable.

## Installing the Standalone Executable (Releases)

1.  **Download**: Go to the Releases page (e.g., on GitHub) and download `transcriptor.exe`.
2.  **Run**: Double-click `transcriptor.exe` to launch the application.
3.  **Requirements**:
    *   **PDF Backend**: For PDF invoice generation, you need a PDF rendering backend.

    **Recommended for Windows: Playwright**
    ```powershell
    pip install playwright
    playwright install
    ```

    *   **GTK3 Runtime (Alternative)**: If using WeasyPrint backend, install GTK3 runtime libraries.
        *   Download and install the latest "GTK3 Runtime Environment" from [GTK-for-Windows-Runtime-Environment-Installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases).
        *   Restart your computer after installing GTK3.

## Building from Source (For Developers)

If you want to build the executable yourself:

1.  **Install Python**: Ensure Python 3.9+ is installed.
2.  **Install Build Tools**:
    ```powershell
    pip install pyinstaller uv
    ```
3.  **Build**:
    Run the provided PowerShell script:
    ```powershell
    .\scripts\build_windows_exe.ps1
    ```
    Or run PyInstaller manually:
    ```powershell
    pyinstaller transcriptor.spec
    ```
    The executable will be generated in the `dist` folder.

## Alternative: Using `uv` (For Command Line Users)

If you are comfortable with the command line:

1.  **Install `uv`**:
    ```powershell
    irm https://astral.sh/uv/install.ps1 | iex
    ```
2.  **Install Transcriptor**:
    ```powershell
    uv tool install . --force
    ```
3.  **Run**:
    ```powershell
    trans5
    ```
