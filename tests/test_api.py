from pathlib import Path
import shutil
import pytest
from io import StringIO
from transcriptor.api import Api
from transcriptor.models import *
from transcriptor.utils import *

BASE_DIR = Path(__file__).parent.joinpath("data")

@pytest.fixture()
def test_config():
    date_format = "%m-%d-%Y"
    base_dir = BASE_DIR
    config = ConfigModel(date_format, base_dir)
    return config

@pytest.fixture()
def test_profile():
    first_name = "Fname"
    last_name = "Lname"
    area = "Area"
    country = "Country"
    return ProfileModel(first_name, last_name, area, country)

@pytest.fixture()
def test_client():
    name = "Client"
    email = "clientemail@gmail.com"
    rates = {"Normal": 0.4, "Expedite": 0.5, "Interpreted": 0.3}
    return ClientModel(name, email, rates)

api = Api()

class TestApi:
    def setup_class(self):
        shutil.rmtree(BASE_DIR, ignore_errors=True)
        BASE_DIR.mkdir(parents=True, exist_ok=True)

    def teardown_class(self):
        shutil.rmtree(BASE_DIR, ignore_errors=True)

    def test_save_config(self, test_config):
        fd = StringIO()
        api.save_config(test_config, fd)
        assert test_config == ConfigModel(**json.loads(fd.getvalue()))

    def test_load_config(self):
        config_file = BASE_DIR.joinpath("config")
        assert isinstance(api.load_config(config_file), ConfigModel)

    def test_default_config(self):
        config_file = BASE_DIR.joinpath("config")
        date_format = "%Y-%m-%d"
        default_config = ConfigModel(date_format, BASE_DIR.joinpath('transcriptor3'))
        assert api.default_config(config_file) == default_config

    def test_edit_config(self, test_config):
        fd = StringIO()
        api.save_config(test_config, fd)
        fd.seek(0) # Seek to start position (Ovewrite existing data)
        api.edit_config(fd, {"date_format": "%d-%m-%Y"})
        assert json.loads(fd.getvalue())['date_format'] == "%d-%m-%Y"

    def test_save_profile(self, test_profile):
        fd = StringIO()
        api.save_profile(test_profile, fd)
        assert test_profile == ProfileModel(**json.loads(fd.getvalue()))

    def test_load_profile(self):
        profile_file = BASE_DIR.joinpath("profile")
        assert isinstance(api.load_profile(profile_file), ProfileModel)

    def test_edit_profile(self, test_profile):
        fd = StringIO()
        api.save_profile(test_profile, fd)
        fd.seek(0) # Seek to start position (Ovewrite existing data)
        api.edit_profile(fd, {"first_name": "Fname2"})
        assert json.loads(fd.getvalue())['last_name'] == "Lname"
        assert json.loads(fd.getvalue())['first_name'] == "Fname2"

    def test_create_client(self):
        name, email, rates = ("name", "email@gmail.com", {"Normal": 0.4, "Expedite": 0.5, "Interpreted": 0.3})
        client = api.create_client(name, email, rates)
        assert isinstance(client, ClientModel)
        assert client.name == 'name'

    def test_save_client(self, test_client):
        api.save_client(test_client, BASE_DIR)
        client_file = BASE_DIR.joinpath("clients", f"{test_client.name}", f"{test_client.name}_info.pickle")
        with open(client_file, 'rb') as fd:
            assert test_client == pickle.load(fd)

    def test_delete_client(self, test_client):
        api.save_client(test_client, BASE_DIR)
        api.delete_client(test_client, BASE_DIR)
        client_file = BASE_DIR.joinpath("clients", f"{test_client.name}", f"{test_client.name}_info.pickle")
        assert not client_file.exists()
        assert client_file.parent.is_dir()
        api.delete_client(test_client, BASE_DIR, purge=True)
        assert not client_file.parent.exists()

    def test_edit_client(self, test_client):
        update_info = {"name": "Updated Client", "email": "updatedclient@email.com"}
        api.save_client(test_client, BASE_DIR)
        api.edit_client(test_client, update_info, BASE_DIR)
        client_file = BASE_DIR.joinpath("clients", f"{sc(update_info['name'])}", f"{sc(update_info['name'])}_info.pickle")
        with open(client_file, 'rb') as fd:
            updated_client = pickle.load(fd)
            assert test_client != updated_client
            assert updated_client.name == "Updated Client"
