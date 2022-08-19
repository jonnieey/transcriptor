import pickle
import json
from appdirs import *

from models import *
from view import *
from controller import *
from utils import *


class Base:
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state


class Transcriptor(Base):
    APP_NAME = 'transcriptor3'
    AUTHOR = 'garagaza'
    config_path = get_config_path(APP_NAME)
    config_file = config_path.joinpath('config')

    def __init__(self, config=None, profile=None):
        super().__init__()
        if config:
            self.config = config
        else:
            if not hasattr(self, "config"):
                self.config = self.load_config()

        if profile:
            self.profile = profile
        else:
            if not hasattr(self, "profile"):
                self.profile = self.load_profile()

    def save_config(self, config):
        touch(self.config_file)

        with open(self.config_file, 'w') as fd:
            config.save(fd)

    def load_config(self):
        try:
            with open(self.config_file, 'r') as fd:
                return ConfigModel(**json.load(fd))
        except FileNotFoundError:
            config = self.default_config()
            self.save_config(config)
            return config

    def default_config(self):
        date_format = "%Y-%m-%d"
        base_dir = user_data_dir(self.APP_NAME, self.AUTHOR )
        default_config = ConfigModel(date_format, base_dir)
        return default_config

    def save_profile(self, profile):
        base_dir = self.config.base_dir
        profile_file = base_dir.joinpath('profile.pickle')
        if not base_dir.exists():
            base_dir.mkdir(parents=True, exist_ok=True)

        with open(profile_file, 'wb') as fd:
            pickle.dump(profile, fd)

    def load_profile(self):
        profile_file = self.config.base_dir.joinpath('profile.pickle')
        try:
            with open(profile_file, 'rb') as fd:
                return pickle.load(fd)
        except FileNotFoundError:
            default_profile = ProfileModel()
            self.save_profile(default_profile)
            return default_profile


def main():
    t = Transcriptor()
    print(t.config.get('date_format'))
    t.config.date_format = "%m-%d-%Y"
    print(t.config.get('date_format'))
    t2 = Transcriptor()
    print(t2.config.get('date_format'))
    config = ConfigModel(date_format="%Y-%m", base_dir="base/dir")
    view = ConsoleView()
    config_controller = Controller(t.config, view)
    config_controller.show_items()
    t.config.set('date_format', '%d-%m')
    print(tuple(t.config))
    profile_controller = Controller(t.profile, view)
    profile_controller.show_items()
    #

if __name__ == "__main__":
    main()
