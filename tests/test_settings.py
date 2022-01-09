import pytest
import io
import json
from transcriptor.settings import Settings
from transcriptor import CLIENTS_FOLDER, JOBS_FOLDER, WORKS_FOLDER

@pytest.fixture()
def default_settings():
    settings = Settings().generate_default_settings()
    return settings

def test_default_settings(default_settings):

    settings_dict = {
        'clients_folder': str(CLIENTS_FOLDER),
        'job_folder': str(JOBS_FOLDER),
        'work_folder': str(WORKS_FOLDER),
    }

    assert default_settings.to_dict() == settings_dict

def test_read_settings_from_file(default_settings):
    fp = io.StringIO(json.dumps(default_settings.to_dict()))

    conf_json = json.load(fp)

    settings_from_file = Settings().from_json(conf_json)

    assert default_settings.to_dict() == settings_from_file.to_dict()


