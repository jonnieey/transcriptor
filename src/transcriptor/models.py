import copy
import json
import pickle
from typing import Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


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
    client: ClientModel
    date_received: date
    job_number: str
    job_type: str
    total_quantity: float
    job_rate: float
    quantity: float
    date_due: date
    job_path: Path
    date_submitted: Optional[date] = None
    status: str = 'Pending'
    amount_paid: float = 0.0
    note: str = ''

    def __iter__(self):
        yield from self.__dict__.items()

    def get(self, attr):
        return getattr(self, attr)

    def set(self, attr, value):
        setattr(self, attr, value)

    item_type = "job"


if __name__ == "__main__":
    client = ClientModel(name="john", email="john@gmail.com", rates={})
    job = JobModel(
        client=client,
        date_received=datetime.strptime("2022-05-05", "%Y-%m-%d"),
        job_number="56321",
        job_type="Normal",
        total_quantity=42.12630,
        job_rate=0.40,
        quantity=21.06315,
        date_due=datetime.strptime("2022-06-01", "%Y-%m-%d"),
        job_path=Path("somerandompath"),
        date_submitted=datetime.strptime("2022-06-01", "%Y-%m-%d"),
        status="Done",
        amount_paid=0.0,
        note="",
    )
    # print(dict(job))
    # print(list(job))
