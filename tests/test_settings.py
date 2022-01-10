import pytest
import io
import json
from transcriptor.settings import Settings
from transcriptor.utils import create_default_config, save_config_to_file
from transcriptor.conf import TEST_CLIENTS_FOLDER, TEST_JOBS_FOLDER, TEST_WORKS_FOLDER, TEST_DATE_FMT, TEST_CONFIG_FOLDER

@pytest.fixture()
def default_config():
    settings = create_default_config()
    return settings

def test_default_settings(default_config):

    settings_dict = {
        'clients_folder': str(TEST_CLIENTS_FOLDER),
        'jobs_folder': str(TEST_JOBS_FOLDER),
        'works_folder': str(TEST_WORKS_FOLDER),
        'date_fmt': str(TEST_DATE_FMT),
        'config_folder': str(TEST_CONFIG_FOLDER)
    }

    assert default_config.to_dict() == settings_dict

def test_save_config_to_file(default_config):
    save_config_to_file(default_config)
    with open(TEST_CONFIG_FOLDER / 'conf.json', 'r') as fp:
        config_json = json.load(fp)
    settings = Settings().from_json(config_json)

    assert (TEST_CONFIG_FOLDER / 'conf.json').exists()
    assert isinstance(settings, Settings)

def test_read_settings_from_file(default_config):
    save_config_to_file(default_config)
    with open(TEST_CONFIG_FOLDER / 'conf.json', 'r') as fp:
        config_json = json.load(fp)
    settings = Settings().from_json(config_json)
    assert settings.config_folder == TEST_CONFIG_FOLDER
