# Transcriptor: Transcription Job Management

Transcriptor is a command-line and TUI application built with Python for managing transcription jobs.  It allows you to track assigned jobs per client, generate invoices, and manage client and job data efficiently.

## Key Features

* **Job Tracking:** Track key job details such as date received, date due, job type, quantity, rate, status, amounts.
* **Client Management:** Add, edit, delete, and view client information, including associated rates.
* **Invoice Generation:** Generate invoices based on completed jobs, with customizable templates and the ability to select a previous cutoff date for summary invoices.
* **CLI Interface:**  Interact with Transcriptor using a powerful and intuitive command-line interface built with `cmd2`.
* **Database Integration:**  Persistent storage of data using SQLite, ensuring data persistence between sessions.
* **Automated File Handling:**  Automatically creates directories for organizing client data, job files and invoices.


## Technologies Used

* **Python:** Programming language.
* **SQLAlchemy:**  Object-Relational Mapper (ORM) for database interactions.
* **SQLite:**  Lightweight and cross-platform database system.
* **cmd2:**  Framework for creating advanced command-line applications.
* **Textual:** Modern terminal UI framework.
* **Jinja2:** Templating engine for invoice generation.
* **WeasyPrint:** HTML to PDF rendering for invoices.
* **Python-Docx:** For processing docx files.
* **Other libraries:** `appdirs`, `audioread`, `markdownify`, `PyYAML`, `rich`, `pydantic`, `platformdirs`.


## Prerequisites

Before installing Transcriptor, ensure you have the following:

* Python 3.9 or higher.
* `poetry` installed (`pip install poetry`)


## Installation

1. **Clone the repository:**

```bash
git clone https://github.com/jonnieey/transcriptor.git
cd transcriptor
```

2. **Install dependencies:**

```bash
poetry install
```

3. **Run the application:**

```bash
poetry run trans5  #This will launch the CLI interface.
```

4. **Install application**

```bash
pipx install .
```

## Usage Examples (CLI)

The Transcriptor CLI uses a simple command structure.  Here are some examples:

* **Show Configuration:**  `show config`

* **Show Profile:** `show profile`

* **Add a Client:** `add client -n "Anderson" -e "anderson@example.com"`

* **Add a Job:**

```bash
    add job --client_id 1 --file "/path/to/your/audio/file.mp3" --job_number 123456 --date_received '2024-03-01' --date_due 2024-03-08 --work_on_file y --job_type Normal --job_template zd --notes "some notes" --quantity 60
```


* **Show Clients:** `show clients`

* **Show Jobs:** `show jobs -w status=Pending`

* **Update a Job:** `update jobs -v status=Done -v amount_paid=25.0 -w id=1`

* **Generate Invoice:** (Requires client_id and conditions for selecting jobs, or the -S flag for summary invoices)

```bash
    # generate a PDF file of invoice
    invoice -c 1 -w date_submitted>="2024-01-01" -w date_submitted<="2024-01-31" -t blue

    # generates summary invoice
    invoice -c 1 -S
```

* **Delete a Client:**

```bash
    # Use with caution!  The `-P` flag will also delete associated files)
    delete clients -w name=Anderson -P
```

* **Purge Job Files:**

```bash
    (Deletes media files and directories according to the given criteria)
    purge -w status=Done
```


## Configuration

The configuration file (`config.yaml`) located in the  `$XDG_CONFIG_DIR or ~/.config` directory, is in YAML format and contains the following options:

* `base_dir`: The base directory for storing all data (default: user data directory).
* `date_format`: The date format used throughout the application (default: "%Y-%m-%d").

You can modify the configuration file directly or using the CLI command `update config`.


## Project Structure

```
transcriptor/
├── src/                      # Source code
│   └── transcriptor/         # Main application module
│       ├── ...               # Modules for API, models, UI
│       └── invoice_templates # Contains HTML templates for invoice generations.
├── tests/                    # Unit tests
│   ├── ...                   # tests main application modules
├── README.md                 # README file
└── pyproject.toml            # Project settings file
```

## License

[MIT License](./LICENSE)
