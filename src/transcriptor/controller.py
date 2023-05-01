import logging
import shutil
from decimal import Decimal
from pathlib import Path
from typing import IO, Any, List, Optional, Sequence, Tuple

import yaml
from sqlalchemy import select, text
from sqlalchemy.engine.row import Row
from sqlalchemy.orm import Session

from transcriptor.database import Base, Database
from transcriptor.models import (
    ClientModel,
    ConfigModel,
    JobModel,
    ProfileModel,
    RatesModel,
)
from transcriptor.utils import mkdirp, sc, truncate

logger = logging.getLogger(__name__)


class API:
    """
    API for the transcriptor app.

    Contains operation functions of the applications. Communication to DB, etc
    """

    def __init__(self, base_dir: str | Path = ".", db_path: str = "transcriptor.db"):

        self.base_dir = Path(base_dir)
        mkdirp([self.base_dir])

        self.db = Database(self.base_dir.joinpath(db_path))
        Base.metadata.create_all(self.db.engine)

    @property
    def session(self) -> Session:
        return Session(self.db.engine)

    @session.setter
    def session(self, session):
        self.db.session = session

    def save_object(self, obj, fd: IO[str]) -> object:
        """
        Save instance of object to file object

        Arguments:
            obj: Object. (Instance of a Model)
            fd: File object

        Returns:
            Object. (Instance of a Model)
        """
        obj.save(fd)
        return obj

    def load_object(self, obj, fd: IO[str]) -> Optional[object]:
        """
        Load instance of object from file object

        Arguments:
            obj: Object. (Instance of a Model)
            fd: File object

        Returns:
            Object. (Instance of a Model)
        """
        obj_dict = yaml.safe_load(fd)
        if obj_dict is None:
            new_obj = obj()
            new_obj.save(fd)
            return new_obj
        try:
            return obj(**obj_dict)
        except TypeError as error:
            logger.error(error)
            return None

    def save_config(self, obj: ConfigModel, fd: IO[str]) -> object:
        """
        Save configuration object to file

        Arguments:
            obj: Object. (Instance of a ConfigModel)
            fd: File object

        Returns:
            ConfigModel instance
        """
        logger.info("Save config")
        config = self.save_object(obj, fd)
        return config

    # def load_config(self):
    def load_config(self, fd: IO[str]) -> object:
        """
        Load configuration object from file

        Arguments:
            fd: File object

        Returns:
            ConfigModel instance
        """
        logger.info("Load config")
        config = self.load_object(ConfigModel, fd)
        return config

    def save_profile(self, obj: object, fd: IO[str]) -> object:
        """
        Save profile object to file

        Arguments:
            obj: Object. (Instance of a ProfileModel)
            fd: File object

        Returns:
            ProfileModel instance
        """
        logger.info("Save profile")
        profile = self.save_object(obj, fd)
        return profile

    def load_profile(self, fd: IO[str]) -> object:
        """
        Load profile object from file

        Arguments:
            fd: File object

        Returns:
            ProfileModel instance
        """

        profile = self.load_object(ProfileModel, fd)
        return profile

    def create_client(
        self,
        name: str,
        email: str,
        rates: dict = {"normal": 0.40, "interpreted": 0.30, "expedite": 0.60},
    ) -> object:
        """
        Create client object

        Arguments
            name: Client's name.
            email: Client's email.
            rates: Client's rates. (dict) ex. {"normal": 0.40, "interpreted": 0.30, "expedite": 0.60}

        Returns:
            ClientModel object
        """

        # logger.info(f'Creating client "{name}"')
        rates = {k: float(v) for k, v in rates.items()}
        rate_obj = RatesModel(**rates)
        client = ClientModel(name=name, email=email, rates=rate_obj)
        return client

    def save_client(self, client: object) -> None:
        """
        Save client to database:

        Arguments:
            client: ClientModel object
        """
        try:
            with self.session as session:
                session.add(client)
                session.commit()

        except Exception as error:
            logger.error(error)

    def list_clients(
        self, client_id: str = ""
    ) -> Sequence[Row[Tuple[ClientModel, RatesModel]]]:
        """
        Get clients in database.

        Arguments:
            client_id: Client's id. (str)

        Returns:
            List of tuples (ClientObject, RateRobject)
        """

        if client_id == "":
            stmt = select(ClientModel, RatesModel).join(RatesModel)
        else:
            stmt = (
                select(ClientModel, RatesModel)
                .filter(ClientModel.id == client_id)
                .join(RatesModel)
            )

        with self.session as session:
            scalars = session.execute(stmt).all()

        return scalars

    def edit_client(
        self,
        client_id: str,
        name: str = "",
        email: str = "",
        rates: dict = {},
    ) -> None:
        """
        Edit client attributes.

        Arguments:
            client_id: Id of client to modify/edit.
            name: Client's new name
            email: Client's new email
            rates: Client's new rates. Dictionary with keys "normal", "expedite", "interpreted".
        """
        with self.session as session:
            client = session.execute(
                select(ClientModel).filter(ClientModel.id == client_id)
            ).scalar_one()
            if client:
                if rates:
                    rates_model = client.rates
                    if "normal" in rates:
                        rates_model.normal = rates["normal"]
                    if "expedite" in rates:
                        rates_model.expedite = rates["expedite"]
                    if "interpreted" in rates:
                        rates_model.interpreted = rates["interpreted"]
                if name:
                    # TODO move client's folder to match new name
                    client.name = name
                if email:
                    client.email = email
                session.commit()

    def delete_client(self, client_id) -> None:
        """
        Delete client from database.

        Arguments:
            client_id: client id to delete.
        """
        with self.session as session:
            c = session.execute(
                select(ClientModel).filter_by(id=f"{client_id}")
            ).scalar_one()
            session.delete(c)
            session.commit()

    def create_job(
        self,
        client_id: int,
        date_received: str,
        job_number: str,
        job_type: str,
        total_quantity: float,
        job_rate: float,
        quantity: float,
        date_due: str,
        job_path: str,
        note: str = "",
    ) -> object:
        """
        Create JobModel object.

        Arguments:
            client_id: Client's id
            date_received: Date received
            job_number: Job number
            job_type: Job type
            total_quantity: Job total quantity
            job_rate: Job rate
            quantity: Job quantity
            date_due: Date due
            job_path: Job path
            note: Job note

        Returns:
            JobModel object
        """

        # logger.info(f"Creating new job {job_number}")

        amount = float(job_rate) * float(quantity)
        amount = truncate(amount, 2)

        job = JobModel(
            client_id=client_id,
            date_received=date_received,
            job_number=job_number,
            job_type=job_type,
            total_quantity=round(Decimal(total_quantity), 1),
            quantity=round(Decimal(quantity), 1),
            job_rate=job_rate,
            amount=round(Decimal(amount), 2),
            date_due=date_due,
            job_path=job_path,
            note=note,
        )
        return job

    def save_job(self, job: object) -> None:
        """
        Save job to database:

        Arguments:
            job: JobModel object
        """
        with self.session as session:
            session.add(job)
            session.commit()

    def list_jobs(self, attributes={}) -> Sequence[Row[Tuple[JobModel]]]:
        """
        Get jobs in database.

        Arguments:
            None

        Returns:
            Tuple of (tuple(Columns), List[tuple(Row)])
        """
        if not attributes:
            stmt = select(JobModel)
        else:
            stmt = select(JobModel).filter_by(**attributes)

        with self.session as session:
            scalars = session.execute(stmt).fetchall()

        return scalars

    def get_job(self, job_id: str | int) -> list[Optional[Row[Tuple[JobModel]]]]:
        """
        Get job from database.

        Arguments:
            job_id: Job's id

        Returns:
            List of Scalars (tuple(Columns, Row))
        """
        stmt = select(JobModel).filter(JobModel.id == job_id)
        with self.session as session:
            scalars = session.execute(stmt).fetchone()
        return [scalars]

    def edit_job(self, **kwargs) -> None:
        """
        Edit job attributes.

        Arguments:
            **kwargs: keyword arguments with job attributes ex. job_number=2, quantity=40.0

        """
        job_id = kwargs.pop("job_id", None)
        if not job_id:
            raise ValueError("job_id is required")

        with self.session as session:
            job_model, client_model = (
                session.query(JobModel, ClientModel)
                .join(ClientModel)
                .filter(JobModel.id == job_id)
                .one_or_none()
            )
            if not job_model:
                raise ValueError(f"Job with id={job_id} does not exist")

            # Update calculated attributes
            # or "job_rate" in kwargs or "quantity" in kwargs:
            if "client_id" in kwargs:
                client_id = kwargs.pop("client_id", job_model.client_id)
                if not client_id:
                    raise ValueError("client_id is required")

                query = (
                    session.query(ClientModel, RatesModel)
                    .join(RatesModel)
                    .filter(ClientModel.id == client_id)
                    .one_or_none()
                )
                if query is not None:
                    new_client_model, new_rates_model = query

                    if not new_client_model or not new_rates_model:
                        raise ValueError(
                            f"Client with id={client_id} does not exist or has no rates"
                        )

                    new_job_rate = kwargs.pop(
                        "job_rate", getattr(new_rates_model, job_model.job_type.lower())
                    )

                    new_quantity = kwargs.pop("quantity", job_model.quantity)

                    if not new_job_rate or not new_quantity:
                        raise ValueError("job_rate and quantity are required")

                    new_quantity = round(Decimal(new_quantity), 1)
                    new_amount = round(Decimal(new_job_rate) * new_quantity, 2)

                    setattr(job_model, "job_rate", new_job_rate)
                    setattr(job_model, "quantity", new_quantity)
                    setattr(job_model, "amount", new_amount)

                    setattr(job_model, "client_id", client_id)

                    original_dir = Path(job_model.job_path)
                    # split path into parts
                    nd = list(original_dir.parts)
                    # replace part after clients (client_name) with new client
                    nd[nd.index("clients") + 1] = sc(new_client_model.name)
                    # convert new list back to path object
                    new_job_dir = Path(*nd)
                    shutil.copytree(original_dir, new_job_dir, dirs_exist_ok=True)
                    setattr(job_model, "job_path", str(new_job_dir))
                    shutil.rmtree(original_dir, ignore_errors=True)

            if "job_type" in kwargs:
                job_type = kwargs.pop("job_type", "")
                client_id = getattr(job_model, "client_id")

                if "job_rate" in kwargs:
                    job_rate = kwargs.pop("job_rate")

                else:
                    query = (
                        session.query(ClientModel, RatesModel)
                        .join(RatesModel)
                        .filter(ClientModel.id == client_id)
                        .one_or_none()
                    )
                    if query is not None:
                        new_client_model, new_rates_model = query
                        job_rate = getattr(new_rates_model, job_type.lower())
                    else:
                        job_rate = None

                if job_rate is not None:
                    quantity = kwargs.pop("quantity", job_model.quantity)
                    new_quantity = round(Decimal(quantity), 1)
                    new_amount = round(Decimal(job_rate) * new_quantity, 2)

                    setattr(job_model, "quantity", new_quantity)
                    setattr(job_model, "amount", new_amount)

                setattr(job_model, "job_type", job_type)
                setattr(job_model, "job_rate", job_rate)

            if "job_rate" in kwargs or "quantity" in kwargs:
                job_rate = kwargs.pop("job_rate", job_model.job_rate)
                quantity = kwargs.pop("quantity", job_model.quantity)
                if not job_rate or not quantity:
                    raise ValueError("job_rate and quantity are required")

                job_type = job_model.job_type
                new_quantity = round(Decimal(quantity), 1)
                new_amount = round(Decimal(job_rate) * new_quantity, 2)

                setattr(job_model, "job_rate", job_rate)
                setattr(job_model, "quantity", new_quantity)
                setattr(job_model, "amount", new_amount)

            if "date_submitted" in kwargs:
                date_submitted = kwargs.pop("date_submitted", "")
                if not date_submitted:
                    status = "Pending"
                else:
                    status = "Done"

                setattr(job_model, "date_submitted", date_submitted)
                setattr(job_model, "status", status)

            # Update job attributes
            if "amount_paid" in kwargs:
                amount_paid = kwargs.pop("amount_paid", "")
                if amount_paid > job_model.amount:
                    amount_paid = job_model.amount
                setattr(job_model, "amount_paid", amount_paid)

            for attr, value in kwargs.items():
                if value is not None:
                    setattr(job_model, attr, value)

            session.commit()

    def delete_job(self, job_id: int | str) -> None:
        """
        Delete job from database.

        Arguments:
            client_name: Name of client to delete.
        """
        with self.session as session:
            job = session.execute(
                select(JobModel).filter_by(id=f"{job_id}")
            ).scalar_one()
            session.delete(job)
            session.commit()

    def execute_sql(self, s):
        stmt = text(s)
        with self.session as session:
            return session.execute(stmt)

    def execute_orm_stmt(self, stmt):
        with self.session as session:
            return session.execute(stmt)

    def get_jobs_scalars_total(self, jobs_list: List[dict[str, Any]]):
        # TODO get totals from sqlite
        amount = 0
        amount_paid = 0
        for job in jobs_list:
            if isinstance(job, Row):
                job = job._mapping["JobModel"].__dict__
            amount += job.get("amount", 0)
            amount_paid += job.get("amount_paid", 0)

        return (truncate(round(amount, 2), 2), truncate(round(amount_paid, 2), 2))

    def create_invoice_data(
        self, client_id: int, period_start, period_end
    ) -> tuple[Any, Any, Any]:
        # job_rows = self.list_jobs(attributes={"client_id": client_id})
        query = select(JobModel).filter(
            JobModel.client_id == client_id,
            JobModel.date_submitted > period_start,
            JobModel.date_submitted <= period_end,
            JobModel.amount > JobModel.amount_paid,
        )
        client_query = select(ClientModel).where(ClientModel.id == client_id)
        with self.session as session:
            job_rows = session.execute(query).scalars()
            client_row = session.execute(client_query).scalars()

            jobs_list = [job_row.__dict__ for job_row in job_rows]
            totals = self.get_jobs_scalars_total(jobs_list)

            client = client_row.all()[0].__dict__

        return (client, jobs_list, totals)

    def remove_media_files(self):
        """
        remove all media files from job directory of paid jobs
        """
        with self.session as session:
            stmt = select(JobModel).filter(JobModel.amount_paid >= JobModel.amount)
            paid_jobs = session.execute(stmt).scalars().all()
            for paid_job in paid_jobs:
                unwanted_files = Path(paid_job.job_path).glob(
                    "**/*[mwzM][p4aiP][3avp3]"
                )

                for unwanted_file in unwanted_files:
                    unwanted_file.unlink(missing_ok=True)


if __name__ == "__main__":
    api = API(base_dir="/home/kamikaze/.local/share/transcriptor3")
    # print(len(api.list_jobs()))
    # print(dir(api.list_jobs()[0]))
    # print([x._mapping["JobModel"] for x in api.list_jobs()])
    # job_rows= api.list_jobs({"client_id": 2})
    # api.create_invoice_data(2, "2022-10-12", "2022-10-30")
    print(api.list_clients())
    # # print(api.get_jobs_scalars_total(jobs))
    # jobs_list = []
    #
    # for job_row in job_rows:
    #     job_dict = job_row._mapping["JobModel"].__dict__
    #     jobs_list.append(job_dict)
    #
    # for job in jobs_list:
    #     print(job["job_number"])
