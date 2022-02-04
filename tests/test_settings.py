import pytest

from transcriptor.conf import (
    TEST_CLIENTS_FOLDER,
    TEST_CONFIG_FOLDER,
    TEST_DATE_FMT,
    TEST_INVOICES_FOLDER,
    TEST_JOBS_FOLDER,
    TEST_RESOURCES_FOLDER,
    TEST_WORKS_FOLDER,
)
from transcriptor.methods import default_settings


@pytest.fixture()
def default_config():
    return default_settings()


def test_default_settings(default_config):

    settings_dict = {
        "clients_folder": str(TEST_CLIENTS_FOLDER),
        "jobs_folder": str(TEST_JOBS_FOLDER),
        "works_folder": str(TEST_WORKS_FOLDER),
        "date_fmt": str(TEST_DATE_FMT),
        "config_folder": str(TEST_CONFIG_FOLDER),
        "invoices_folder": str(TEST_INVOICES_FOLDER),
        "resources_folder": str(TEST_RESOURCES_FOLDER),
    }

    assert default_config.to_dict() == settings_dict


def test_save_config_to_file(default_config):
    pass


def test_read_settings_from_file(default_config):
    pass
