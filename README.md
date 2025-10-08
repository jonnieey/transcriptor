# Transcriptor

A powerful, terminal-based application for managing transcription jobs, clients, and invoices.

## Features

- **Client Management:** Add, update, delete, and view client information.
- **Job Tracking:** Keep track of all your transcription jobs, including details like job number, due dates, quantity, and status.
- **Rate Management:** Assign different rates (normal, expedite, interpreted) to each client.
- **Invoice Generation:** Generate professional invoices in both PDF and CSV formats.
- **Interactive TUI:** A user-friendly Textual User Interface (TUI) for easy management of your data.
- **Powerful CLI:** A command-line interface for scripting and advanced operations.
- **Database Backup and Restore:** Keep your data safe with built-in backup and restore functionality.
- **Configuration:** Customize the application to your needs through a simple configuration file.

## Installation

This project uses `uv` for package management.

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/transcriptor.git
    cd transcriptor
    ```

2.  **Create a virtual environment and install dependencies:**

    ```bash
    uv venv
    source .venv/bin/activate
    uv pip install -e .
    ```

## Usage

The application can be run in two modes: TUI (Textual User Interface) and CLI (Command-Line Interface).

### TUI Mode

The TUI mode provides an interactive and user-friendly interface for managing your transcription business.

To start the TUI, run:

```bash
trans5 tui
```

The TUI has the following tabs:

- **Dashboard:** Shows pending jobs.
- **All Jobs:** Lists all jobs.
- **Cutoffs:** Displays cutoff dates for invoicing.
- **Clients:** Lists all your clients.
- **Rates:** Shows the rates for each client.
- **Configuration:** Allows you to view and edit the application's configuration.

### CLI Mode

The CLI mode is perfect for scripting and performing quick actions.

To start the CLI, run:

```bash
trans5
```

This will open an interactive shell. Here are some of the available commands:

- `show`: Display clients, jobs, rates, and configuration.
- `add`: Add new clients and jobs.
- `update`: Update existing clients, jobs, and rates.
- `delete`: Remove clients and jobs.
- `invoice`: Generate invoices for clients.
- `backup`: Create a backup of the database.
- `restore`: Restore the database from a backup.

For more detailed information on each command, use the `help` command within the CLI.

**Examples:**

- **Show all clients:**

  ```bash
  show clients
  ```

- **Add a new job:**

  ```bash
  add job -f /path/to/job/file.mp3
  ```

- **Generate an invoice for a client:**

  ```bash
  invoice -c 1 -w 'date_submitted > "2025-01-01"' -w 'date_submitted <= "2025-01-31"'
  ```

## Database

The application uses an SQLite database to store all its data. The database file (`transcriptor.db`) is located in the base directory specified in the configuration.

The database schema is defined in `src/transcriptor/models.py` and includes the following tables:

- `clients`: Stores client information.
- `jobs`: Stores job details.
- `rates`: Stores the rates for each client.

The database also uses triggers to automate certain tasks, such as updating the `amount` of a job when the `quantity` or `job_rate` changes.

## Backup and Restore

It's crucial to keep your data safe. The application provides simple commands for backing up and restoring the database.

- **Create a backup:**

  ```bash
  backup
  ```

- **Restore from a backup:**

  ```bash
  restore
  ```

Backups are stored in the `backups` directory within the application's base directory.

## Development

To set up the development environment, install the development dependencies:

```bash
uv pip install -e '.[dev]'
```

### Testing

The project uses `pytest` for testing. To run the tests, use the following command:

```bash
pytest
```

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
