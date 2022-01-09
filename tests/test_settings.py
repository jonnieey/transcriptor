import pytest
import io
import json
from transcriptor.settings import Settings
from transcriptor.conf import TEST_CLIENTS_FOLDER, TEST_JOBS_FOLDER, TEST_WORKS_FOLDER, TEST_DATE_FMT, TEST_CONFIG_FOLDER

@pytest.fixture()
def default_settings():
    settings = Settings().generate_default_settings()
    return settings

def test_default_settings(default_settings):

    settings_dict = {
        'clients_folder': str(TEST_CLIENTS_FOLDER),
        'jobs_folder': str(TEST_JOBS_FOLDER),
        'works_folder': str(TEST_WORKS_FOLDER),
        'date_fmt': str(TEST_DATE_FMT),
        'config_folder': str(TEST_CONFIG_FOLDER)
    }

    assert default_settings.to_dict() == settings_dict

def test_read_settings_from_file(default_settings):
    fp = io.StringIO(json.dumps(default_settings.to_dict()))

    conf_json = json.load(fp)

    settings_from_file = Settings().from_json(conf_json)

    assert default_settings.to_dict() == settings_from_file.to_dict()


