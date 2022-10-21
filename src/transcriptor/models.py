import copy
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import yaml

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
        yaml.dump(dict(config), file_object, sort_keys=False)

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
        yaml.dump(dict(self), file_object, sort_keys=False)

    item_type = "profile"


@dataclass
class ClientModel(Model):
    client_id: str
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
        yaml.dump(dict(self), file_object, sort_keys=False)

    item_type = "client"


@dataclass
class JobModel(Model):
    job_id: str
    client_id: str
    date_received: str
    job_number: str
    job_type: str
    total_quantity: float
    job_rate: float
    quantity: float
    date_due: str
    job_path: str
    date_submitted: str = ""
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
            jobs = [dict(self)]  # new job list
        else:
            file_object.seek(0)
            # jobs = pickle.load(file_object)
            jobs = yaml.safe_load(file_object)
            jobs.append(dict(self))

        file_object.seek(0)
        # pickle.dump(
        #     jobs,
        #     file_object,
        #     protocol=pickle.HIGHEST_PROTOCOL,
        # )
        yaml.safe_dump(jobs, file_object, sort_keys=False)

    item_type = "job"
