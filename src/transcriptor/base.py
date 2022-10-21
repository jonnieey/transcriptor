import json
import pickle

from transcriptor.api import API
from transcriptor.controller import Controller
from transcriptor.models import *
from transcriptor.utils import *
from transcriptor.view import ConsoleView


class Base:
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state


class Transcriptor(Base, API):
    APP_NAME = "transcriptor3"

    def __init__(self):

        self.config = self.load_config(self.APP_NAME)
        self.base_dir = self.config.base_dir
        self.clients_dir = self.config.base_dir.joinpath("clients")
        self.profile_file = self.config.base_dir.joinpath("profile")
