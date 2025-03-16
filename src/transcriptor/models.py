from dataclasses import dataclass
import yaml
from abc import ABC
from sqlalchemy import String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import event
from sqlalchemy import DDL


class Base(DeclarativeBase):
    pass


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    rate: Mapped["Rate"] = relationship(
        "Rate",
        uselist=False,
        cascade="all, delete-orphan",
        back_populates="client",
    )
    jobs: Mapped[list["Job"]] = relationship(
        "Job", back_populates="client", cascade="all, delete-orphan"
    )


class Rate(Base):
    __tablename__ = "rates"
    id: Mapped[int] = mapped_column(primary_key=True)
    normal: Mapped[float] = mapped_column(nullable=False)
    expedite: Mapped[float] = mapped_column(nullable=False)
    interpreted: Mapped[float] = mapped_column(nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"))
    client: Mapped[Client] = relationship(
        "Client", back_populates="rate", passive_deletes=True
    )


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"))
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
    client: Mapped[Client] = relationship("Client", back_populates="jobs")


update_amount_trigger = DDL(
    """
    CREATE TRIGGER IF NOT EXISTS update_amount
    AFTER UPDATE OF job_rate, quantity ON Jobs
    BEGIN
        UPDATE Jobs
        SET amount = ROUND(NEW.quantity * NEW.job_rate, 2)
        WHERE id = NEW.id;
    END;
    """
)

event.listen(
    Job.__table__, "after_create", update_amount_trigger.execute_if(dialect="sqlite")
)

update_date_trigger = DDL(
    """
    CREATE TRIGGER IF NOT EXISTS update_date
        AFTER UPDATE OF status ON Jobs
    BEGIN
        UPDATE Jobs
        SET 
            date_submitted = CASE
                WHEN NEW.status = 'Pending' THEN NULL
                WHEN NEW.status = 'Done' AND NEW.date_submitted IS NULL THEN DATE("NOW", 'localtime')
                ELSE date_submitted
            END
            WHERE id = NEW.id;
    END;
    """
)

event.listen(
    Job.__table__, "after_create", update_date_trigger.execute_if(dialect="sqlite")
)

update_status_trigger = DDL(
    """
    CREATE TRIGGER IF NOT EXISTS update_status
        AFTER UPDATE OF date_submitted ON Jobs
    BEGIN
        UPDATE Jobs
        SET 
            status = CASE
                WHEN NEW.date_submitted IS NULL THEN 'Pending'
                WHEN NEW.date_submitted IS '' THEN 'Pending'
                WHEN DATE(NEW.date_submitted) IS NOT NULL THEN 'Done'
                ELSE status
            END
            WHERE id = NEW.id;
    END;
    """
)
event.listen(
    Job.__table__, "after_create", update_status_trigger.execute_if(dialect="sqlite")
)
limit_amount_paid_trigger = DDL(
    """
    CREATE TRIGGER IF NOT EXISTS limit_amounts_paid
        AFTER UPDATE OF amount_paid ON Jobs
    BEGIN
        UPDATE Jobs
        SET
            amount_paid = (
                CASE 
                    WHEN NEW.amount_paid > Jobs.amount THEN Jobs.amount
                    ELSE NEW.amount_paid
                END
            )
            WHERE Jobs.id = New.id;
    END;
    """
)
event.listen(
    Job.__table__,
    "after_create",
    limit_amount_paid_trigger.execute_if(dialect="sqlite"),
)

update_job_rates_trigger = DDL(
    """ 
    CREATE TRIGGER IF NOT EXISTS update_job_rates
        AFTER UPDATE OF client_id ON Jobs
    BEGIN
        UPDATE Jobs
            SET job_rate = CASE
                WHEN LOWER(job_type) = 'normal' THEN (SELECT normal FROM Rates WHERE Rates.id = New.client_id)
                WHEN LOWER(job_type) = 'expedite' THEN (SELECT expedite FROM Rates WHERE Rates.id = New.client_id)
                WHEN LOWER(job_type) = 'interpreted' THEN (SELECT interpreted FROM Rates WHERE Rates.id = New.client_id)
                ELSE job_rate
            END
        WHERE id = NEW.id;
    END;
    """
)
event.listen(
    Job.__table__,
    "after_create",
    update_job_rates_trigger.execute_if(dialect="sqlite"),
)


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
