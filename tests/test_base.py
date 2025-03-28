import shutil
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from transcriptor.api import API
from transcriptor.base import Transcriptor
from transcriptor.models import Config

# Constants for testing
TEST_BASE_DIR = Path(__file__).parent / "test_transcriptor_data"
CONFIG_FILE = TEST_BASE_DIR / "config.yaml"
PROFILE_FILE = TEST_BASE_DIR / "profile.yaml"


@pytest.fixture(scope="module")
def test_base_dir():
    # Setup
    test_dir = TEST_BASE_DIR
    test_dir.mkdir(exist_ok=True)
    yield test_dir
    # Teardown
    shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture
def clean_config(test_base_dir):
    # Ensure clean config for each test
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
    yield
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()


@pytest.fixture
def clean_profile(test_base_dir):
    # Ensure clean profile for each test
    if PROFILE_FILE.exists():
        PROFILE_FILE.unlink()
    yield
    if PROFILE_FILE.exists():
        PROFILE_FILE.unlink()


@pytest.fixture
def default_config():
    return {"base_dir": str(TEST_BASE_DIR), "date_format": "%Y-%m-%d"}


@pytest.fixture
def default_profile():
    return {"name": "", "area": "", "country": ""}


@pytest.fixture
def transcriptor(test_base_dir, clean_config, clean_profile, default_config):
    # Create a fresh Transcriptor instance for each test
    config = Config(**default_config)
    t = Transcriptor(config=config, config_file=CONFIG_FILE)
    return t


def test_initialization(
    transcriptor, test_base_dir, default_config, default_profile
):
    """Test Transcriptor initializes with default config and profile"""
    # Verify config
    assert transcriptor.config.base_dir == str(test_base_dir)
    assert transcriptor.config.date_format == default_config["date_format"]
    assert CONFIG_FILE.exists()

    # Verify profile
    assert transcriptor.profile.name == default_profile["name"]
    assert transcriptor.profile.area == default_profile["area"]
    assert transcriptor.profile.country == default_profile["country"]
    assert PROFILE_FILE.exists()

    # Verify API initialization
    assert isinstance(transcriptor.api, API)
    assert transcriptor.api.base_dir == test_base_dir


def test_initialization_with_existing_config(test_base_dir, default_config):
    """Test initialization with existing config file"""
    # Create existing config
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(default_config, f)

    transcriptor = Transcriptor(config_file=CONFIG_FILE)

    assert transcriptor.config.base_dir == str(test_base_dir)
    assert transcriptor.config.date_format == default_config["date_format"]


def test_initialization_with_existing_profile(test_base_dir, default_profile):
    """Test initialization with existing profile file"""
    profile_data = {
        "name": "Test User",
        "area": "Test Area",
        "country": "Test Country",
    }
    # Create existing profile
    with open(PROFILE_FILE, "w") as f:
        yaml.dump(profile_data, f)

    transcriptor = Transcriptor(config_file=CONFIG_FILE)

    assert transcriptor.profile.name == profile_data["name"]
    assert transcriptor.profile.area == profile_data["area"]
    assert transcriptor.profile.country == profile_data["country"]


def test_save_config(transcriptor, test_base_dir):
    """Test saving config updates the file"""
    new_date_format = "%d-%m-%Y"
    transcriptor.config.date_format = new_date_format
    transcriptor.save_config(CONFIG_FILE)

    # Verify file was updated
    with open(CONFIG_FILE, "r") as f:
        saved_config = yaml.safe_load(f)
    assert saved_config["date_format"] == new_date_format


def test_save_profile(transcriptor, test_base_dir):
    """Test saving profile updates the file"""
    new_name = "Updated Name"
    transcriptor.profile.name = new_name
    transcriptor.save_profile(PROFILE_FILE)

    # Verify file was updated
    with open(PROFILE_FILE, "r") as f:
        saved_profile = yaml.safe_load(f)
    assert saved_profile["name"] == new_name


def test_create_client(transcriptor, test_base_dir):
    """Test client creation with default rates"""
    client_name = "Test Client"
    client_email = "test@example.com"

    transcriptor.create_client(name=client_name, email=client_email)

    # Verify client was created in database
    clients = transcriptor.api.get_clients(
        conditions={"name": [("=", client_name)]}
    )
    assert len(clients) == 1
    assert clients[0]["name"] == client_name
    assert clients[0]["email"] == client_email

    # Verify rates were created
    rates = transcriptor.api.get_rates(
        conditions={"client_id": [("=", clients[0]["id"])]}
    )
    assert len(rates) == 1
    assert rates[0]["normal"] == 0.4
    assert rates[0]["expedite"] == 0.6
    assert rates[0]["interpreted"] == 0.3

    # Verify client directory was created
    client_dir = test_base_dir / "clients" / "Test_Client"
    assert client_dir.exists()
    assert (client_dir / "templates").exists()


def test_create_client_with_custom_rates(transcriptor, test_base_dir):
    """Test client creation with custom rates"""
    client_name = "Custom Rate Client"
    client_email = "custom@example.com"
    custom_rates = {"normal": 0.5, "expedite": 0.7, "interpreted": 0.4}

    transcriptor.create_client(
        name=client_name, email=client_email, rates_dict=custom_rates
    )

    # Verify custom rates were set
    clients = transcriptor.api.get_clients(
        conditions={"name": [("=", client_name)]}
    )
    rates = transcriptor.api.get_rates(
        conditions={"client_id": [("=", clients[0]["id"])]}
    )
    assert rates[0]["normal"] == 0.5
    assert rates[0]["expedite"] == 0.7
    assert rates[0]["interpreted"] == 0.4


def test_create_job_dir(transcriptor, test_base_dir):
    """Test job directory creation"""
    client_name = "JobDirTest"
    job_number = "JOB123"
    date_received = "2023-06-15"
    date_due = "2023-06-20"

    # First create the client
    transcriptor.create_client(name=client_name, email="jobdir@test.com")

    job_dir = transcriptor.create_job_dir(
        client_name=client_name,
        job_number=job_number,
        date_received=date_received,
        date_due=date_due,
    )

    # Verify directory structure
    assert job_dir.exists()
    assert str(job_dir).endswith("15_Thu_JOB123_DUE_20_Tue")
    assert job_dir.parent.name == "June"
    assert job_dir.parent.parent.name == "2023"


@patch("transcriptor.base.shutil.copy")
@patch("transcriptor.base.shutil.copytree")
def test_mv_extract_job_file(mock_copytree, mock_copy, transcriptor):
    """Test job file movement/extraction"""
    test_file = Path("test_file.zip")
    test_dir = Path("test_dir")

    # Test with zip file
    with patch("transcriptor.base.zipfile.is_zipfile", return_value=True):
        with patch("transcriptor.base.zipfile.ZipFile") as mock_zip:
            transcriptor.mv_extract_job_file(test_file, test_dir)
            mock_zip.assert_called_once_with(test_file)

    # Test with regular file
    with patch("transcriptor.base.zipfile.is_zipfile", return_value=False):
        transcriptor.mv_extract_job_file(test_file, test_dir)
        mock_copy.assert_called_once_with(test_file, test_dir)


def test_select_job_template(transcriptor, test_base_dir):
    """Test job template selection"""
    client_name = "TemplateTest"
    transcriptor.create_client(name=client_name, email="template@test.com")

    # Test with valid template
    template_path = transcriptor.select_job_template(client_name, "zd")
    assert template_path.exists()
    assert template_path.name == "Zoom Deposition Block Files.docx"

    # Test template directory was created
    client_template_dir = (
        test_base_dir / "clients" / "TemplateTest" / "templates"
    )
    assert client_template_dir.exists()


def test_generate_invoice(transcriptor):
    """Test invoice generation"""
    # Setup test client and jobs
    client_id = transcriptor.api.add_client(
        {"name": "InvoiceClient", "email": "invoice@test.com"}
    )
    job_data = {
        "client_id": client_id,
        "date_received": "2023-01-01",
        "job_number": "INV001",
        "job_type": "Normal",
        "status": "Done",
        "date_due": "2023-01-10",
        "total_quantity": 60.0,
        "quantity": 60.0,
        "job_rate": 0.4,
        "amount": 24.0,
        "amount_paid": 0.0,
        "job_path": "/path/to/job",
        "note": "Test invoice job",
        "date_submitted": "2023-01-05",
    }
    transcriptor.api.add_job(job_data)

    # Generate invoice
    html, client_name = transcriptor.generate_invoice(
        client_id=client_id,
        conditions={"amount_paid": [("=", 0)]},
        invoice_theme="blue",
    )

    assert client_name == "InvoiceClient"
    assert "InvoiceClient" in html
    assert "INV001" in html
    assert "24.0" in html


@patch("transcriptor.utils.HTML.write_pdf")
def test_html_to_pdf(mock_write_pdf, transcriptor, test_base_dir):
    """Test HTML to PDF conversion"""
    test_html = "<html><body>Test</body></html>"
    client_name = "PDFClient"

    transcriptor.html_to_pdf(test_html, client_name)

    # Verify directory was created
    invoice_dir = test_base_dir / "clients" / "PDFClient" / "invoices"
    assert invoice_dir.exists()

    # Verify PDF would be created with today's date
    today = date.today().strftime("%Y-%m-%d")
    invoice_dir / f"{today}_PDFClient_invoice.pdf"
    mock_write_pdf.assert_called_once()


def test_save_and_load_cutoffs(transcriptor, test_base_dir):
    """Test cutoff date saving and loading"""
    test_cutoffs = [
        ["Cutoff Date", "Deposit Date"],
        [date(2023, 1, 15), date(2023, 1, 20)],
        [date(2023, 2, 15), date(2023, 2, 20)],
    ]

    # Save cutoffs
    transcriptor.save_cutoffs(test_cutoffs)

    # Verify file was created
    cutoff_file = test_base_dir / "cutoffs" / "cutoffs_2025.csv"
    assert cutoff_file.exists()

    # Load cutoffs
    loaded_cutoffs = transcriptor.load_cutoffs()
    assert len(loaded_cutoffs) == 3
    assert loaded_cutoffs[1][0] == date(2023, 1, 15)
    assert loaded_cutoffs[2][1] == date(2023, 2, 20)


def test_select_cutoff_period(transcriptor):
    """Test cutoff period selection"""
    test_cutoffs = [
        [date(2023, 1, 15), date(2023, 1, 20)],
        [date(2023, 2, 15), date(2023, 2, 20)],
        [date(2023, 3, 15), date(2023, 3, 20)],
    ]

    # Mock loaded cutoffs
    # Test first period
    prev, curr = transcriptor.select_cutoff_period(1, cutoffs=test_cutoffs)
    assert prev is None
    assert curr == date(2023, 1, 15)

    # Test middle period
    prev, curr = transcriptor.select_cutoff_period(2, cutoffs=test_cutoffs)
    assert prev == date(2023, 1, 15)
    assert curr == date(2023, 2, 15)

    # Test last period
    prev, curr = transcriptor.select_cutoff_period(3, cutoffs=test_cutoffs)
    assert prev == date(2023, 2, 15)
    assert curr == date(2023, 3, 15)


def test_delete_clients_with_purge(transcriptor, test_base_dir):
    """Test client deletion with purge option"""
    client_name = "DeleteClient"
    transcriptor.create_client(name=client_name, email="delete@test.com")

    # Verify client exists
    clients = transcriptor.api.get_clients(
        conditions={"name": [("=", client_name)]}
    )
    assert len(clients) == 1

    # Delete with purge
    deleted = transcriptor.delete_clients(
        conditions={"name": [("=", client_name)]}, purge=True
    )

    assert len(deleted) == 1
    assert deleted[0]["name"] == client_name

    # Verify client directory was removed
    client_dir = test_base_dir / "clients" / "DeleteClient"
    assert not client_dir.exists()


def test_delete_jobs_with_purge(transcriptor, test_base_dir):
    """Test job deletion with purge option"""
    # Setup client and job
    client_id = transcriptor.api.add_client(
        {"name": "JobDeleteTest", "email": "jobdelete@test.com"}
    )
    job_data = {
        "client_id": client_id,
        "date_received": "2023-01-01",
        "job_number": "DEL001",
        "job_type": "Normal",
        "status": "Done",
        "date_due": "2023-01-10",
        "total_quantity": 60.0,
        "quantity": 60.0,
        "job_rate": 0.4,
        "amount": 24.0,
        "amount_paid": 0.0,
        "job_path": str(test_base_dir / "test_job_path"),
        "note": "Test job to delete",
        "date_submitted": "2023-01-05",
    }
    job_id = transcriptor.api.add_job(job_data)

    # Create dummy job directory
    job_dir = test_base_dir / "test_job_path"
    job_dir.mkdir(parents=True)

    # Delete with purge
    deleted = transcriptor.delete_jobs(
        conditions={"id": [("=", job_id)]}, purge=True
    )

    assert len(deleted) == 1
    assert not job_dir.exists()
