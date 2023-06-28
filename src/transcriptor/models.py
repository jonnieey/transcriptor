from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import yaml

from transcriptor.utils import touch


class Model(ABC):
    @abstractmethod
    def get(self, item):
        pass

    @property
    @abstractmethod
    def item_type(self):
        pass

    def cols(self):
        return list(self.__dict__.keys())

    def rows(self):
        return list(self.__dict__.values())


class Environment(Enum):
    DEV = "dev"
    DEVEL = "devel"


@dataclass
class ConfigModel(Model):
    date_format: str = ""
    base_dir: str = ""

    def __iter__(self):
        yield from self.__dict__.items()

    def get(self, attr):
        return getattr(self, attr)

    def set(self, attr, value):
        setattr(self, attr, value)

    def save(self, file_object):
        yaml.safe_dump(dict(self), file_object, sort_keys=True)

    item_type = "config"


@dataclass
class ProfileModel(Model):
    first_name: str = ""
    last_name: str = ""
    area: str = ""
    country: str = ""

    def __iter__(self):
        yield from self.__dict__.items()

    def get(self, attr):
        return getattr(self, attr)

    def set(self, attr, value):
        setattr(self, attr, value)

    def save(self, file_object):
        yaml.safe_dump(dict(self), file_object, sort_keys=False)

    def from_file(self, file_path: str | Path):
        try:
            with open(file_path, "r") as fd:
                obj_dict = yaml.safe_load(fd)
                for attr, value in obj_dict.items():
                    setattr(self, attr, value)
                return self
        except FileNotFoundError:
            touch([file_path])
            with open(file_path, "w") as fd:
                self.save(fd)
                return self

    item_type = "profile"
