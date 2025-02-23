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


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str] = mapped_column(nullable=False)
    area: Mapped[str] = mapped_column(nullable=False)
    country: Mapped[str] = mapped_column(nullable=False)


class Config(Base):
    __tablename__ = "configs"
    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(nullable=False)
    value: Mapped[str] = mapped_column(nullable=False)
