import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from transcriptor.api import API
from transcriptor.cli import TranscriptorCMD
from transcriptor.models import Config, Profile

# Constants for testing
TEST_BASE_DIR = Path(__file__).parent / "test_cli_data"
CONFIG_FILE = TEST_BASE_DIR / "config.yaml"
PROFILE_FILE = TEST_BASE_DIR / "profile.yaml"
HISTORY_FILE = TEST_BASE_DIR / ".history"


@pytest.fixture(scope="module")
def test_base_dir():
    # Setup
    test_dir = TEST_BASE_DIR
    test_dir.mkdir(exist_ok=True)
    yield test_dir
    # Teardown
    shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture
def mock_transcriptor(test_base_dir):
    # Create a mock Transcriptor instance
    config = Config(
        base_dir=str(test_base_dir),
        date_format="%Y-%m-%d",
        invoice_theme="default",
    )
    profile = Profile()

    with patch("transcriptor.cli.Transcriptor", autospec=True) as mock:
        mock.return_value.config = config
        mock.return_value.profile = profile
        mock.return_value.base_dir = test_base_dir
        mock.return_value.CONFIG_DIR = test_base_dir
        mock.return_value.api = MagicMock(spec=API)
        yield mock


@pytest.fixture
def cli_app(mock_transcriptor, test_base_dir):
    # Mock the persistent history file operations
    app = TranscriptorCMD(
        history=False, alias=True
    )  # Disable history for tests
    yield app

    # Clean up after test
    if hasattr(app, "app"):
        del app.app


def test_cli_initialization(cli_app, mock_transcriptor):
    """Test CLI application initialization"""
    assert isinstance(cli_app, TranscriptorCMD)
    mock_transcriptor.assert_called_once()
    assert hasattr(cli_app, "app")
    assert cli_app.debug is True


def test_do_show_config(cli_app, mock_transcriptor):
    """Test 'show config' command"""
    # Mock the view's print_table method
    with patch("transcriptor.cli.TranscriptorView.print_table") as mock_print:
        result = cli_app.onecmd("show config")
        assert result is False
        mock_print.assert_called_once_with(
            mock_transcriptor.return_value.config.__dict__
        )


def test_do_show_profile(cli_app, mock_transcriptor):
    """Test 'show profile' command"""
    with patch("transcriptor.cli.TranscriptorView.print_table") as mock_print:
        result = cli_app.onecmd("show profile")
        assert result is False
        mock_print.assert_called_once_with(
            mock_transcriptor.return_value.profile.__dict__
        )


def test_do_show_clients(cli_app, mock_transcriptor):
    """Test 'show clients' command"""
    mock_clients = [
        {"id": 1, "name": "Test Client", "email": "test@example.com"}
    ]
    mock_transcriptor.return_value.api.get_clients.return_value = mock_clients

    with patch("transcriptor.cli.TranscriptorView.print_table") as mock_print:
        result = cli_app.onecmd("show clients")
        assert result is False
        mock_print.assert_called_once_with(
            mock_clients, orientation="horizontal"
        )


def test_do_show_clients_with_conditions(cli_app, mock_transcriptor):
    """Test 'show clients' with conditions"""
    mock_transcriptor.return_value.api.get_clients.return_value = []

    with patch("transcriptor.cli.parse_conditions") as mock_parse:
        mock_parse.return_value = {"name": [("=", "Test")]}
        cli_app.onecmd("show clients -w name=Test")
        mock_transcriptor.return_value.api.get_clients.assert_called_once_with(
            conditions={"name": [("=", "Test")]}
        )


def test_do_add_client(cli_app, mock_transcriptor):
    """Test 'add client' command"""
    # Mock user input
    with patch(
        "transcriptor.cli.prompt",
        side_effect=["Test Client", "test@example.com"],
    ):
        result = cli_app.onecmd(
            "add client -n 'Test Client' -e 'test@example.com'"
        )
        assert result is False
        cli_app.app.create_client.assert_called_once()


def test_do_add_job(cli_app, mock_transcriptor):
    """Test 'add job' command"""
    # Setup mocks
    mock_client = MagicMock()
    mock_client.id = 1
    mock_client.name = "Test Client"
    mock_client.email = "test@example.com"

    cli_app.app.api.get_clients.return_value = [mock_client]

    # Mock file operations
    mock_file = MagicMock()
    mock_file.name = "test_file.mp3"

    # Mock input handler file path and info methods
    mock_path = MagicMock()
    mock_path.exists.return_value = True
    cli_app.input_handler.get_job_file_path = MagicMock(
        return_value=mock_path
    )
    cli_app.input_handler.get_job_info = MagicMock(
        return_value={
            "client_id": 1,
            "job_number": "JOB001",
            "date_received": "2023-01-01",
            "date_due": "2023-01-10",
        }
    )
    cli_app.input_handler.get_task_info = MagicMock(
        return_value={
            "job_template": "zd",
            "job_type": "Normal",
            "quantity": "60",
            "note": "Cannot be late",
            "total_quantity": 60,
        }
    )

    # Mock user input
    input_sequence = {
        "client_id": "1",
        "job_number": "JOB001",
        "date_received": "2023-01-01",
        "date_due": "2023-01-10",
        "work_on_file": "y",
        "job_type": "Normal",
        "quantity": "60",
        "job_template": "zd",
        "note": "'Cannot be late'",
    }

    with patch("transcriptor.cli.prompt", side_effect=input_sequence):
        command = "add job -f test_file.mp3 -c {} -j {} -r {} -d {} -w {} -t {} -q {} -T {} -N {}".format(
            *[v for k, v in input_sequence.items()]
        )
        result = cli_app.onecmd(command)
        assert result is False
        cli_app.app.create_job.assert_called_once()


def test_do_update_config(cli_app, mock_transcriptor):
    """Test 'update config' command"""
    result = cli_app.onecmd("update config --date-format %d-%m-%Y")
    assert result is False
    assert mock_transcriptor.return_value.config.date_format == "%d-%m-%Y"
    mock_transcriptor.return_value.save_config.assert_called_once()


def test_do_update_profile(cli_app, mock_transcriptor):
    """Test 'update profile' command"""
    result = cli_app.onecmd("update profile --name 'Test User'")
    assert result is False
    assert mock_transcriptor.return_value.profile.name == "Test User"
    mock_transcriptor.return_value.save_profile.assert_called_once()


def test_do_delete_clients(cli_app, mock_transcriptor):
    """Test 'delete clients' command"""
    mock_transcriptor.return_value.api.get_clients.return_value = [
        {"id": 1, "name": "Test Client"}
    ]

    with patch("transcriptor.cli.prompt", side_effect=["y", "Test Client"]):
        result = cli_app.onecmd("delete clients -w name=Test")
        assert result is False
        mock_transcriptor.return_value.delete_clients.assert_called_once()


def test_do_invoice(cli_app, mock_transcriptor):
    """Test 'invoice' command"""
    mock_client = MagicMock()
    mock_client.id = 1
    mock_client.name = "Test Client"

    cli_app.app.api.get_clients.return_value = [mock_client]
    cli_app.app.get_invoice_jobs.return_value = []
    cli_app.app.generate_invoice.return_value = (
        "<html>Test</html>",
        "Test Client",
    )

    with patch("transcriptor.cli.prompt", return_value="1"):
        result = cli_app.onecmd("invoice -c 1 -w client_id=1")
        assert result is False
        cli_app.app.generate_invoice.assert_called_once()


def test_do_invoice_summary(cli_app, mock_transcriptor):
    """Test summary invoice generation"""
    mock_client = MagicMock()
    mock_client.id = 1
    mock_client.name = "Test Client"

    cli_app.app.api.get_clients.return_value = [mock_client]
    # Return a dict to emulate summary invoice structure
    cli_app.app.get_summary_invoice_jobs.return_value = {"Test Client": []}
    cli_app.app.generate_summary_invoice.return_value = (
        "<html>Summary</html>",
        "Test Client",
    )

    with patch("transcriptor.cli.prompt", return_value="1"):
        result = cli_app.onecmd("invoice -c 1 -S")
        assert result is False
        cli_app.app.generate_summary_invoice.assert_called_once()


def test_do_purge(cli_app, mock_transcriptor):
    """Test 'purge' command"""
    mock_jobs = [{"id": 1, "job_path": "test/path"}]
    mock_transcriptor.return_value.api.get_jobs.return_value = mock_jobs

    with patch("transcriptor.cli.prompt", return_value="y"):
        result = cli_app.onecmd("purge -w id=1")
        assert result is False
        mock_transcriptor.return_value.purge_job_files.assert_called_once_with(
            mock_jobs
        )


def test_do_exit(cli_app):
    """Test exit command"""
    with patch("transcriptor.cli.TranscriptorCMD.poutput"):
        result = cli_app.onecmd("exit")
        assert result is True


def test_do_quit(cli_app):
    """Test quit command"""
    with patch("transcriptor.cli.TranscriptorCMD.poutput"):
        result = cli_app.onecmd("quit")
        assert result is True


def test_do_EOF(cli_app):
    """Test EOF command"""
    with patch("transcriptor.cli.TranscriptorCMD.poutput"):
        result = cli_app.onecmd("EOF")
        assert result is True


def test_emptyline(cli_app):
    """Test empty line input"""
    result = cli_app.emptyline()
    assert result is None


def test_do_clear(cli_app):
    """Test clear command"""
    with patch("transcriptor.cli.os.system") as mock_system:
        result = cli_app.onecmd("clear")
        assert result is False
        mock_system.assert_called_once_with("clear")
