import json
import pickle

from appdirs import user_data_dir

from transcriptor.controller import Controller
from transcriptor.models import ConfigModel, ProfileModel
from transcriptor.new_handlers import Api
from transcriptor.utils import *
from transcriptor.view import ConsoleView


class Base:
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state


class Transcriptor(Base, Api):
    APP_NAME = "transcriptor3"
    AUTHOR = "garagaza"
    config_path = get_config_path(APP_NAME)
    config_file = config_path.joinpath("config")

    def __init__(self, config=None, profile=None, api=None):
        super().__init__()
        if config:
            self.config = config
        else:
            if not hasattr(self, "config"):
                self.config = self.load_config()

        self.base_dir = self.config.base_dir
        self.clients_dir = self.config.base_dir.joinpath("clients")
        self.profile_file = self.config.base_dir.joinpath("profile")

        if profile:
            self.profile = profile
        else:
            if not hasattr(self, "profile"):
                self.profile = self.load_profile()

    def save_config(self, config):
        touch(self.config_file)

        with open(self.config_file, "w") as fd:
            config.save(fd)

    def load_config(self):
        try:
            with open(self.config_file, "r") as fd:
                return ConfigModel(**json.load(fd))
        except FileNotFoundError:
            config = self.default_config()
            self.save_config(config)
            return config

    def default_config(self):
        date_format = "%Y-%m-%d"
        base_dir = user_data_dir(self.APP_NAME, self.AUTHOR)
        default_config = ConfigModel(date_format, base_dir)
        return default_config

    def save_profile(self, profile):
        touch(self.profile_file)

        with open(self.profile_file, "w") as fd:
            profile.save(fd)

    def load_profile(self):
        try:
            with open(self.profile_file, "r") as fd:
                return ProfileModel(**json.load(fd))
        except FileNotFoundError:
            profile = ProfileModel()
            self.save_profile(profile)
            return profile


def main():
    t = Transcriptor()
    client = t.create_client(
        name="test client",
        email="testclient@gmail.com",
        rates={"Normal": 0.4, "Expedite": 0.6, "Interpreted": 0.3},
    )
    t.save_client(client)
    t.edit_client(client, update_dict={"name": "test update"})
    view = ConsoleView()
    client_controller = Controller(client, view)
    client_controller.show_items()
    # t.delete_client(client)
    # print(t.config.get('date_format'))
    # t.config.date_format = "%m-%d-%Y"
    # print(t.config.get('date_format'))
    # t2 = Transcriptor()
    # print(t2.config.get('date_format'))
    # config = ConfigModel(date_format="%Y-%m", base_dir="base/dir")
    # view = ConsoleView()
    # config_controller = Controller(t.config, view)
    # config_controller.show_items()
    # t.config.set('date_format', '%d-%m')
    # print(tuple(t.config))
    # profile_controller = Controller(t.profile, view)
    # profile_controller.show_items()


if __name__ == "__main__":
    main()
