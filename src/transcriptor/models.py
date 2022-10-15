import copy
import json
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional
from transcriptor.utils import sc
TODAY = datetime.today()
YEAR = TODAY.year


class Model(ABC):
    @abstractmethod
    def get(self, item):
        pass

    @property
    @abstractmethod
    def item_type(self):
        pass


@dataclass
class ConfigModel(Model):
    date_format: str
    base_dir: Path

    def __post_init__(self):
        self.base_dir = Path(self.base_dir)

    def __iter__(self):
        yield from self.__dict__.items()

    def get(self, attr):
        return getattr(self, attr)

    def set(self, attr, value):
        setattr(self, attr, value)

    def save(self, file_object, indent=2):
        config = copy.copy(self)
        config.base_dir = str(config.base_dir)
        json.dump(dict(config), file_object, indent=indent)

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

    def save(self, file_object, indent=2):
        json.dump(dict(self), file_object, indent=indent)

    item_type = "profile"


@dataclass
class ClientModel(Model):
    name: str
    email: str
    rates: dict

    def __iter__(self):
        yield from self.__dict__.items()

    def get(self, attr):
        return getattr(self, attr)

    def set(self, attr, value):
        setattr(self, attr, value)

    def save(self, file_object):
        pickle.dump(self, file_object)

    item_type = "client"


@dataclass
class JobModel(Model):
    client: ClientModel = None
    date_received: date = None
    job_number: str = ""
    job_type: str = ""
    total_quantity: float = 0.0
    job_rate: float = 0.0
    quantity: float = 0.0
    date_due: date = None
    job_path: Path = None
    date_submitted: Optional[date] = None
    status: str = "Pending"
    amount_paid: float = 0.0
    note: str = ""

    def __iter__(self):
        yield from self.__dict__.items()

    def get(self, attr):
        return getattr(self, attr)

    def set(self, attr, value):
        setattr(self, attr, value)

    def save(self, file_object) -> None:
        """
        Save job object as pickle to file.

        Arguments:
            file_object: Open file buffer

        """
        # seek(pos, whence=[0, 1, 2]) 0:start of stream , 2: Curr pos, 2: End of stream
        file_object.seek(0, 2)
        if file_object.tell() == 0:
            jobs = [self]  # new job list
        else:
            file_object.seek(0)
            jobs = pickle.load(file_object)
            jobs.append(self)

        file_object.seek(0)
        pickle.dump(
            jobs,
            file_object,
            protocol=pickle.HIGHEST_PROTOCOL,
        )

    item_type = "job"

