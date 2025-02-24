import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from transcriptor.base import Transcriptor, DEFAULT_CONFIG
from transcriptor.utils import sc


@pytest.fixture
def mock_config(tmp_path):
    return MagicMock(base_dir=f"{tmp_path}/data", date_format="%Y-%m-%d")


@pytest.fixture
def transcriptor(mock_config):
    transcriptor = Transcriptor(config=mock_config)
    return transcriptor


@pytest.fixture
def mock_api():
    return MagicMock()


def test_initialization_with_default_config(tmp_path):
    with patch("transcriptor.base.ConfigModel") as MockConfigModel:
        instance = MockConfigModel()
        instance.base_dir = DEFAULT_CONFIG["base_dir"]
        instance.date_format = DEFAULT_CONFIG["date_format"]
        MockConfigModel.from_yaml.return_value = instance

        transcriptor_instance = Transcriptor(config=None)
        assert transcriptor_instance.config.base_dir == DEFAULT_CONFIG["base_dir"]
        assert transcriptor_instance.config.date_format == DEFAULT_CONFIG["date_format"]


def test_create_client(transcriptor):
    transcriptor.api = MagicMock()
    client_name = "Test Client"
    email = "test@example.com"

    # Create client
    transcriptor.create_client(client_name, email)

    # Assertions
    transcriptor.api.add_client.assert_called_once_with(
        {"name": client_name, "email": email}
    )
    transcriptor.api.add_rates.assert_called_once()
    client_dir = Path(transcriptor.base_dir, "clients", sc(client_name))
    assert client_dir.is_dir()


def test_create_job_dir(transcriptor, mock_config):
    client_name = "Client"
    job_num = "123"
    date_received = "2023-01-10"
    date_due = "2023-02-10"

    job_directory = transcriptor.create_job_dir(
        client_name, job_num, date_received, date_due
    )
    assert job_directory.is_dir()


def test_mv_extract_job_file(tmp_path):
    job_file = tmp_path / "fake.zip"
    job_dir = tmp_path / "jobdir"
    job_file.touch()  # Create the file
    job_dir.mkdir()

    with patch("zipfile.is_zipfile", return_value=True), patch(
        "zipfile.ZipFile"
    ) as MockZipFile:
        mock_instance = MockZipFile.return_value
        mock_instance.__enter__.return_value = (
            mock_instance  # Supports context management
        )
        mock_instance.extractall = MagicMock()

        Transcriptor.mv_extract_job_file(job_file, job_dir)
        mock_instance.extractall.assert_called_once_with(job_dir)


def test_select_job_template(transcriptor, tmp_path):
    client_name = "Client"
    template_initials = "TMP"
    mock_template_dir = tmp_path / "templates"
    mock_template_dir.mkdir(parents=True, exist_ok=True)

    # Mock template mapping and copy function
    with patch.dict(
        "transcriptor.base.TEMPLATE_MAPPING", {template_initials: "template_file.ext"}
    ):
        template_path = transcriptor.select_job_template(client_name, template_initials)

        # Assertion
        assert (
            template_path
            == transcriptor.base_dir
            / "clients"
            / sc(client_name)
            / "templates"
            / "template_file.ext"
        )
