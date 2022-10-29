import json
import pickle
from typing import Any, Dict

from appdirs import user_config_dir, user_data_dir

from transcriptor.api import API
from transcriptor.controller import Controller
from transcriptor.models import *
from transcriptor.utils import *
from transcriptor.view import ConsoleView


class Base:
    _shared_state: Dict[Any, Any] = {}

    def __init__(self):
        self.__dict__ = self._shared_state


class Transcriptor(Base, API):
    APP_NAME = "transcriptor3"

    def __init__(self):

        self.config = self.get_config()
        self.base_dir = mkdirp(Path(self.config.base_dir))
        self.clients_dir = mkdirp(self.base_dir.joinpath("clients"))

    def get_config(self):
        CONFIG_DIR = Path(user_config_dir(appname=self.APP_NAME))
        CONFIG_FILE = CONFIG_DIR.joinpath("config.yml")

        if not CONFIG_FILE.exists():
            touch(CONFIG_FILE)
            default_config = self.default_config()
            with open(CONFIG_FILE, "w") as fd:
                config = self.save_config(default_config, fd)
                return config

        with open(CONFIG_FILE, "r") as fd:
            return ConfigModel(**yaml.safe_load(fd))

    def get_profile(self):
        PROFILE_FILE = self.base_dir.joinpath("profile")

        if not PROFILE_FILE.exists():
            touch(PROFILE_FILE)
            profile = ProfileModel()
            with open(PROFILE_FILE, "w") as fd:
                self.save_profile(profile, fd)

        with open(PROFILE_FILE, "r") as fd:
            return self.load_profile(ProfileModel, fd)

    def add_client(
        self, name, email, rates={"Normal": 0.40, "Expedite": 0.60, "Interpreted": 0.30}
    ):
        CLIENT_FILE = self.clients_dir.joinpath(sc(name)).joinpath(f"{sc(name)}.yml")
        if not CLIENT_FILE.exists():
            touch(CLIENT_FILE)

        new_client = self.create_client(name, email, rates)
        with open(CLIENT_FILE, "w") as fd:
            self.save_client(new_client, fd)


if __name__ == "__main__":
    app = Transcriptor()
    # create Profile
    app.get_profile()
    client_name = "John"
    client_email = "Johnnjahi@gmail.com"
    # app.add_client(client_name, client_email)
    client = [x for x in app.get_client_by_attr("name", client_name, app.clients_dir)][
        0
    ]
    job = app.create_job(
        client_id=client.client_id,
        date_received="2022-05-05",
        job_number="56321",
        job_type="Normal",
        total_quantity="42.12630",
        job_rate="0.40",
        quantity="21.06315",
        date_due="2022-06-01",
        job_path="somerandompath",
    )
    job_file = app.clients_dir.joinpath(sc(client.name)).joinpath("jobs.yml")
    if not job_file.exists():
        touch(job_file)
    with open(job_file, "r+") as fd:
        app.save_job(job, fd)
