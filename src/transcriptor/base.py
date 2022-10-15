import json
import pickle

from transcriptor.api import Api
from transcriptor.controller import Controller
from transcriptor.models import *
from transcriptor.utils import *
from transcriptor.view import ConsoleView


class Base:
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state

class Transcriptor(Base, Api):
    APP_NAME = "transcriptor3"
    AUTHOR = "jonnieey"
    config_path = get_config_path(APP_NAME)
    config_file = config_path.joinpath("config")

    def __init__(self, config=None, profile=None):
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
