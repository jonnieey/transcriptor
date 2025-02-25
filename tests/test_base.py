import pytest
import shutil
import zipfile
from transcriptor.base import (
    Transcriptor,
    DEFAULT_CONFIG,
    CONFIG_FILE_NAME,
)
from transcriptor.models import ConfigModel
from transcriptor.utils import TEMPLATE_MAPPING, get_media_files
from transcriptor.utils import str_to_date as std
from unittest.mock import patch


# Mock API for testing
class MockAPI:
    def __init__(self, base_dir=None):
        self.clients = []
        self.rates = []
        self.jobs = []
        self.base_dir = base_dir

    def add_client(self, client_dict):
        client_id = len(self.clients) + 1
        client_dict["id"] = client_id
        self.clients.append(client_dict)
        return client_id

    def add_rates(self, rates_dict):
        self.rates.append(rates_dict)

    def get_clients(self, conditions):
        if (
            not isinstance(conditions, set)
            or len(conditions) != 2
            or "id" not in conditions
        ):
            return None

        client_id = None
        for item in conditions:
            if isinstance(item, int):
                client_id = item
                break

        if client_id is None:
            return None

        for client in self.clients:
            if client["id"] == client_id:
                return type("Client", (object,), client)
        return None

    def get_rates(self, conditions):
        for rate in self.rates:
            if rate["client_id"] == conditions["client_id"]:
                return type("Rates", (object,), rate)
        return None

    def add_jobs(self, jobs):
        self.jobs.extend(jobs)


# Fixtures
@pytest.fixture
def temp_config_dir(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    Transcriptor.CONFIG_DIR = config_dir
    Transcriptor.CONFIG_FILE = config_dir / CONFIG_FILE_NAME
    yield config_dir
    shutil.rmtree(config_dir)


@pytest.fixture
def temp_base_dir(tmp_path):
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    yield base_dir
    shutil.rmtree(base_dir)


@pytest.fixture
def transcriptor_instance(temp_base_dir, temp_config_dir):
    mock_api = MockAPI(base_dir=temp_base_dir)
    transcriptor = Transcriptor(api=mock_api, config=ConfigModel(**DEFAULT_CONFIG))
    transcriptor.config.base_dir = str(temp_base_dir)
    transcriptor.base_dir = temp_base_dir
    return transcriptor


# Tests for __init__
def test_init_default_config(temp_config_dir):
    transcriptor = Transcriptor()
    assert transcriptor.config.base_dir == DEFAULT_CONFIG["base_dir"]
    assert transcriptor.config.date_format == DEFAULT_CONFIG["date_format"]
    assert Transcriptor.CONFIG_FILE.exists()


def test_init_existing_config(temp_config_dir):
    config_file = Transcriptor.CONFIG_FILE
    config = ConfigModel(base_dir="test", date_format="%d-%m-%Y")
    config.write(config_file)
    transcriptor = Transcriptor()
    assert transcriptor.config.base_dir == "test"
    assert transcriptor.config.date_format == "%d-%m-%Y"


def test_init_provided_config(temp_base_dir):
    config = ConfigModel(base_dir=str(temp_base_dir), date_format="%d-%m-%Y")
    transcriptor = Transcriptor(config=config)
    assert transcriptor.config.base_dir == str(temp_base_dir)
    assert transcriptor.config.date_format == "%d-%m-%Y"


# Tests for create_client
def test_create_client(transcriptor_instance, temp_base_dir):
    transcriptor_instance.create_client("Test Client", "test@example.com")
    client_dir = temp_base_dir / "clients" / "Test_Client"
    assert client_dir.exists()
    assert (client_dir / "templates").exists()
    assert len(transcriptor_instance.api.clients) == 1
    assert len(transcriptor_instance.api.rates) == 1
    assert transcriptor_instance.api.clients[0]["name"] == "Test Client"
    assert transcriptor_instance.api.rates[0]["client_id"] == 1


# Tests for create_job_dir
def test_create_job_dir(transcriptor_instance, temp_base_dir):
    job_dir = transcriptor_instance.create_job_dir(
        "Test Client", "123", "2023-10-26", "2023-10-27"
    )
    expected_dir = (
        temp_base_dir
        / "clients"
        / "Test_Client"
        / "2023"
        / "October"
        / "26_Thu_123_DUE_27_Fri"
    )
    assert job_dir == expected_dir
    assert job_dir.exists()


# Tests for mv_extract_job_file
def test_mv_extract_job_file_move(tmp_path):
    job_file = tmp_path / "test.txt"
    job_file.write_text("test content")
    job_dir = tmp_path / "job_dir"
    job_dir.mkdir()
    Transcriptor.mv_extract_job_file(job_file, job_dir)
    assert not job_file.exists()
    assert (job_dir / "test.txt").exists()


def test_mv_extract_job_file_extract(tmp_path):
    job_file = tmp_path / "test.txt"
    job_dir = tmp_path / "job_dir"
    job_dir.mkdir()
    with zipfile.ZipFile(job_file, "w") as zf:
        zf.writestr("inner.txt", "inner content")
    Transcriptor.mv_extract_job_file(job_file, job_dir)
    assert not job_file.exists()
    assert (job_dir / "inner.txt").exists()


# Tests for select_job_template
def test_select_job_template(transcriptor_instance, temp_base_dir):
    template_path = transcriptor_instance.select_job_template("Test Client", "zd")
    expected_path = (
        temp_base_dir / "clients" / "Test_Client" / "templates" / TEMPLATE_MAPPING["zd"]
    )
    assert template_path == expected_path
    assert template_path.exists()


def test_get_media_files(tmp_path):
    (tmp_path / "audio.mp3").write_text("audio")
    (tmp_path / "video.mp4").write_text("video")
    (tmp_path / "other.txt").write_text("other")

    media_files = list(get_media_files(tmp_path))
    assert len(media_files) == 2
    assert (tmp_path / "audio.mp3") in media_files
    assert (tmp_path / "video.mp4") in media_files


# Tests for create_job
def test_create_job(transcriptor_instance, temp_base_dir, tmp_path):
    job_file = tmp_path / "job.txt"
    job_file.write_text("test")
    client_name = "Test Client"
    transcriptor_instance.create_client(client_name, "test@example.com")

    def job_callback(file):
        return {
            "client_id": 1,
            "job_number": "123",
            "date_received": std("2023-10-26", "%Y-%m-%d"),
            "date_due": std("2023-10-27", "%Y-%m-%d"),
        }

    def task_callback(file):
        return {
            "job_type": "normal",
            "quantity": 10,
            "job_template": "zd",
            "note": "test note",
            "total_quantity": 20,
        }

    job_dir = transcriptor_instance.create_job_dir(
        "Test Client", "123", "2023-10-26", "2023-10-27"
    )
    (job_dir / "media1.mp3").write_text("media1")
    (job_dir / "media2.wav").write_text("media2")

    transcriptor_instance.create_job(job_file, job_callback, task_callback)

    assert (job_dir / "123 Due 10.27.docx").exists()
    assert len(transcriptor_instance.api.jobs) == 2
    assert transcriptor_instance.api.jobs[0]["amount"] == 4.0
