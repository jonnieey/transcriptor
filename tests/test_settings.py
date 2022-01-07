import pytest
import io
import json
from transcriptor.settings import Settings
from transcriptor import CLIENT_FOLDER, JOB_FOLDER, WORK_FOLDER

@pytest.fixture()
def default_settings():
    settings = Settings().generate_default_settings()
    return settings

def test_default_settings(default_settings):

    settings_dict = {
        'clients_folder': CLIENT_FOLDER,
        'job_folder': JOB_FOLDER,
        'work_folder': WORK_FOLDER,
    }

    assert default_settings.to_dict() == settings_dict

def test_read_settings_from_file(default_settings):
    fp = io.StringIO(json.dumps(default_settings.to_dict()))

    conf_json = json.load(fp)

    settings_from_file = Settings().from_json(conf_json)

    assert default_settings.to_dict() == settings_from_file.to_dict()


