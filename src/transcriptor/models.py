from abc import ABC, abstractmethod
from dataclasses import dataclass

import yaml
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from transcriptor.database import Base


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
        return self.__dict__.values()


@dataclass
class ConfigModel(Model):
    date_format: str
    base_dir: str

    def __iter__(self):
        yield from self.__dict__.items()

    def get(self, attr):
        return getattr(self, attr)

    def set(self, attr, value):
        setattr(self, attr, value)

    def save(self, file_object):
        yaml.safe_dump(dict(self), file_object, sort_keys=False)

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

    item_type = "profile"


class RatesModel(Base):
    __tablename__ = "Rates"

    id: Mapped[int] = mapped_column(primary_key=True)
    normal: Mapped[float] = mapped_column(default=0.40)
    expedite: Mapped[float] = mapped_column(default=0.60)
    interpreted: Mapped[float] = mapped_column(default=0.30)
    client: Mapped["ClientModel"] = relationship(back_populates="rates")


class ClientModel(Base):
    __tablename__ = "Clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column()
    rates_id: Mapped[int] = mapped_column(ForeignKey("Rates.id"), default="")
    rates: Mapped["RatesModel"] = relationship(back_populates="client")
    jobs: Mapped[list["JobModel"]] = relationship()


class JobModel(Base):
    __tablename__ = "Jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("Clients.id"), nullable=True)
    date_received: Mapped[str] = mapped_column()
    job_number: Mapped[str] = mapped_column()
    job_type: Mapped[str] = mapped_column()
    status: Mapped[str] = mapped_column(default="Pending")
    date_due: Mapped[str] = mapped_column()
    total_quantity: Mapped[float] = mapped_column()
    quantity: Mapped[float] = mapped_column()
    job_rate: Mapped[float] = mapped_column()
    date_submitted: Mapped[str] = mapped_column(default="")
    amount: Mapped[float] = mapped_column(default=0.0)
    amount_paid: Mapped[float] = mapped_column(default=0.0)
    job_path: Mapped[str] = mapped_column(String(100))
    note: Mapped[str] = mapped_column(default="")
