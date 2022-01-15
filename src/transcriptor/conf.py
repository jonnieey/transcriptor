import os
from pathlib import Path

from appdirs import user_config_dir

BASE_DIR = Path("/home/kamikaze/Documents/Wera/Transcription2")
CLIENTS_FOLDER = BASE_DIR / "clients"
JOBS_FOLDER = BASE_DIR / "jobs"
WORKS_FOLDER = BASE_DIR / "work"
CONFIG_FOLDER = Path(user_config_dir("transcriptor"))
INVOICES_FOLDER = BASE_DIR / "invoices"
DATE_FMT = "%Y-%m-%d"

app_config = {
    "base_dir": BASE_DIR,
    "clients_folder": CLIENTS_FOLDER,
    "jobs_folder": JOBS_FOLDER,
    "works_folder": WORKS_FOLDER,
    "config_folder": CONFIG_FOLDER,
    "invoices_folder": INVOICES_FOLDER,
    "date_fmt": DATE_FMT,
}

TEST_BASE_DIR = Path(__file__).parent.parent.parent / "tests" / "data"
TEST_CLIENTS_FOLDER = TEST_BASE_DIR / "clients"
TEST_JOBS_FOLDER = TEST_BASE_DIR / "jobs"
TEST_WORKS_FOLDER = TEST_BASE_DIR / "work"
TEST_CONFIG_FOLDER = TEST_BASE_DIR / ".config" / "transcriptor"
TEST_INVOICES_FOLDER = TEST_BASE_DIR / "invoices"
TEST_DATE_FMT = "%Y-%m-%d"

app_config_test = {
    "base_dir": TEST_BASE_DIR,
    "clients_folder": TEST_CLIENTS_FOLDER,
    "jobs_folder": TEST_JOBS_FOLDER,
    "works_folder": TEST_WORKS_FOLDER,
    "config_folder": TEST_CONFIG_FOLDER,
    "invoices_folder": TEST_INVOICES_FOLDER,
    "date_fmt": TEST_DATE_FMT,
}


def get_config():
    if os.environ.get("TRANSCRIPTOR_TEST", None) == "1":
        return app_config_test
    else:
        return app_config
