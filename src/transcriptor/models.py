from dataclasses import dataclass
import yaml
from abc import ABC
from sqlalchemy import String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)


class Rate(Base):
    __tablename__ = "rates"
    id: Mapped[int] = mapped_column(primary_key=True)
    normal: Mapped[float] = mapped_column(nullable=False)
    expedite: Mapped[float] = mapped_column(nullable=False)
    interpreted: Mapped[float] = mapped_column(nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    client: Mapped[Client] = relationship(cascade="all")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    date_received: Mapped[str] = mapped_column(nullable=False)
    job_number: Mapped[str] = mapped_column(nullable=False)
    job_type: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default="Pending")
    date_due: Mapped[str] = mapped_column(nullable=False)
    total_quantity: Mapped[float] = mapped_column(nullable=False)
    quantity: Mapped[float] = mapped_column(nullable=False)
    job_rate: Mapped[float] = mapped_column(nullable=False)
    date_submitted: Mapped[str] = mapped_column(nullable=True)
    amount: Mapped[float] = mapped_column(nullable=False)
    amount_paid: Mapped[float] = mapped_column(nullable=False, default=0.0)
    job_path: Mapped[str] = mapped_column(nullable=False)
    note: Mapped[str] = mapped_column(nullable=False, default="")


class Model(ABC):
    def get(self, item):
        return getattr(self, item)

    @classmethod
    def from_yaml(cls, yaml_file):
        try:
            with open(yaml_file, "r") as file:
                data = yaml.safe_load(file)
            return cls(**data)
        except FileNotFoundError:
            print(f"Error: YAML file '{yaml_file}' not found.")
            return None
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            return None
        except TypeError as e:
            print(
                f"Error creating {cls.__name__} model: {e}. Check your yaml file structure."
            )
            return None

    def write(self, yaml_file):
        try:
            with open(yaml_file, "w") as file:
                yaml.dump(self.__dict__, file, Dumper=yaml.SafeDumper)
        except FileNotFoundError:
            print(f"Error: Cannot open or create YAML file '{yaml_file}'.")
        except yaml.YAMLError as e:
            print(f"Error writing YAML file: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


@dataclass
class ConfigModel(Model):
    base_dir: str
    date_format: str

    def __repr__(self):
        return str(self.__dict__)


@dataclass
class ProfileModel(Model):
    first_name: str = ""
    last_name: str = ""
    area: str = ""
    country: str = ""
