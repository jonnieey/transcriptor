# Transcriptor

> A powerful, terminal-based application for managing transcription jobs, clients, and professional invoices.

Transcriptor streamlines the workflow for freelance transcribers and small agencies. It provides a centralized system to track jobs, manage client-specific rates, monitor deadlines, and generate professional PDF invoices—all from your terminal.

## Key Features

*   **Dual Interface:**
    *   **TUI (Textual User Interface):** A rich, interactive dashboard powered by [Textual](https://textual.textualize.io/). Features Vim-like navigation, sorting, and direct editing.
    *   **CLI (Command Line Interface):** A scriptable command line tool for quick entry, automation, and piping.
*   **Comprehensive Job Tracking:** Manage job numbers, due dates, audio duration, status (Pending/Done), and file locations.
*   **Client Management:** Maintain a database of clients with specific contact details.
*   **Flexible Rate System:** Define custom rates per client for different job types (Normal, Expedite, Interpreted).
*   **Automated Invoicing:**
    *   Generate PDF and CSV invoices.
    *   Support for multiple invoice themes.
    *   Annual summary generation.
*   **Workflow Automation:** Automatically organizes job files into a structured directory hierarchy based on client and date.
*   **Data Safety:** Built-in SQLite database with automatic backup capabilities.

## Installation

This project uses `uv` for modern, fast Python package management.

### Prerequisites
*   Python 3.9+
*   `uv` (Recommended) or `pip`

### Steps

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/transcriptor.git
    cd transcriptor
    ```

2.  **Install dependencies:**
    ```bash
    # Create virtual environment and install
    uv venv
    source .venv/bin/activate
    uv pip install -e .
    ```

### PDF Backends (Optional)

Transcriptor supports multiple PDF rendering engines. Install one or more backends as needed:

```bash
# Install with Playwright (recommended for Windows)
uv pip install -e '.[playwright]'
playwright install  # Install browser binaries

# Install with WeasyPrint (requires system libraries)
uv pip install -e '.[weasyprint]'

# Install with xhtml2pdf (pure Python, limited CSS)
uv pip install -e '.[xhtml2pdf]'

# Install all backends
uv pip install -e '.[all]'
```

The system will auto-detect available backends with priority: Playwright > WeasyPrint > xhtml2pdf.

You can override the backend selection with the `TRANSCRIPTOR_PDF_BACKEND` environment variable (set to `playwright`, `weasyprint`, or `xhtml2pdf`).

## Usage

### 🖥️ TUI Mode (Interactive Dashboard)

Launch the visual interface:
```bash
trans5 tui
```

**Navigation:**
*   **Tabs:** Dashboard, All Jobs, Cutoffs, Clients, Rates, Configuration.
*   **Vim Mode:** Press `v` to toggle. Use `h` / `l` to switch tabs.
*   **Actions:**
    *   `a`: Add New Job
    *   `e`: Edit Selected Job
    *   `r`: Refresh Table

**Dashboard:** Quickly view and manage pending jobs. Select multiple jobs to perform batch actions.

### ⌨️ CLI Mode (Command Line)

The CLI offers both an interactive shell and one-off command execution.

#### 1. Interactive Shell
Enter the dedicated shell environment:
```bash
trans5
```
Prompt: `(trans5) `

#### 2. One-off Commands
Run commands directly from your system shell. This is ideal for scripts or quick checks. Aliases defined in `.cmd2rc` are loaded silently.
```bash
trans5 cli show version
trans5 cli invoice -c 1 --print
```

#### Common Commands

| Command | Description | Example |
| :--- | :--- | :--- |
| `show` | List data (clients, jobs, rates) | `show clients` |
| `add` | Create new records | `add job -f /path/to/audio.mp3` |
| `update` | Modify existing records | `update job -j 12345 -v status=Done` |
| `delete` | Remove records | `delete job -w id=5` |
| `invoice` | Generate invoices | `invoice -c 1 -w "date_submitted > '2023-01-01'"` |
| `backup` | Backup database | `backup` |

Use `help <command>` for detailed syntax (e.g., `help add`).

## Configuration

Transcriptor uses YAML for configuration.

*   **Config File:** `~/.config/transcriptor/config.yaml` (Linux)
*   **Profile:** `~/.local/share/transcriptor/profile.yaml` (Stores your business details for invoices)

**Default `config.yaml`:**
```yaml
base_dir: /home/user/.local/share/transcriptor
date_format: "%Y-%m-%d"
invoice_theme: default
```

## Database & Structure

Data is stored in an **SQLite** database (`transcriptor.db`) located in your `base_dir`.

**Directory Structure:**
```text
base_dir/
├── clients/
│   └── ClientName/
│       ├── 2023/
│       │   └── Month/
│       │       └── Date_JobNumber_Due/  <-- Job Files Here
│       ├── invoices/
│       └── templates/
├── cutoffs/
├── backups/
└── transcriptor.db
```

## Development

### Setup
Install development dependencies:
```bash
uv pip install -e '.[dev]'
```

### Testing
Run the test suite using `pytest`:
```bash
pytest
```

## License

MIT License. See `LICENSE` for details.

---
