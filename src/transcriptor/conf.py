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

TEST_BASE_DIR = Path(__file__).parent.parent.parent / "tests" / "data"
TEST_CLIENTS_FOLDER = TEST_BASE_DIR / "clients"
TEST_JOBS_FOLDER = TEST_BASE_DIR / "jobs"
TEST_WORKS_FOLDER = TEST_BASE_DIR / "work"
TEST_CONFIG_FOLDER = TEST_BASE_DIR / ".config" / "transcriptor"
TEST_INVOICES_FOLDER = TEST_BASE_DIR / "invoices"
TEST_DATE_FMT = "%Y-%m-%d"

paths = [
    "clients_folder",
    "jobs_folder",
    "works_folder",
    "config_folder",
    "invoices_folder",
    "date_fmt",
]

app_paths = [
    CLIENTS_FOLDER,
    JOBS_FOLDER,
    WORKS_FOLDER,
    CONFIG_FOLDER,
    INVOICES_FOLDER,
    DATE_FMT,
]

tests_paths = [
    TEST_CLIENTS_FOLDER,
    TEST_JOBS_FOLDER,
    TEST_WORKS_FOLDER,
    TEST_CONFIG_FOLDER,
    TEST_INVOICES_FOLDER,
    TEST_DATE_FMT,
]


def get_config() -> dict:
    """
    Get default environment configurations.

    Returns:
        Dictonary with environment configurations.
    """
    if os.environ.get("TRANSCRIPTOR_TEST", None) == "1":
        return dict(zip(paths, tests_paths))
    else:
        return dict(zip(paths, app_paths))
