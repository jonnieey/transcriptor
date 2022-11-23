import logging
from pathlib import Path

import yaml
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from transcriptor.database import Base, Database
from transcriptor.models import *
from transcriptor.utils import *

logger = logging.getLogger(__name__)


class API:
    def __init__(self, base_dir, db_path="transcriptor.db"):

        self.base_dir = Path(base_dir)
        mkdirp([self.base_dir])

        self.db = Database(self.base_dir.joinpath(db_path))
        Base.metadata.create_all(self.db.engine)

    @property
    def session(self):
        return Session(self.db.engine)

    def save_object(self, obj, file_object):
        obj.save(file_object)
        return obj

    def load_object(self, obj, file_object):
        obj_dict = yaml.safe_load(file_object)
        if obj_dict is None:
            return obj()
        try:
            obj = obj(**obj_dict)
            return obj
        except TypeError as error:
            logger.error(error)

    def save_config(self, obj, file_object):
        logger.info("Save config")
        config = self.save_object(obj, file_object)
        return config

    # def load_config(self):
    def load_config(self, fd):
        logger.info("Load config")
        config = self.load_object(ConfigModel, fd)
        return config

    def save_profile(self, obj, fd):
        logger.info("Save profile")
        profile = self.save_object(obj, fd)
        return profile

    def load_profile(self, fd):
        profile = self.load_object(ProfileModel, fd)
        return profile

    def create_client(
        self,
        name: str,
        email: str,
        rates: dict = {"normal": 0.40, "interpreted": 0.30, "expedite": 0.60},
    ):
        logger.info(f'Creating client "{name}"')
        rate_obj = RatesModel(**rates)
        client = ClientModel(name=name, email=email, rates=rate_obj)
        return client

    def save_client(self, client: ClientModel):
        try:
            with self.session as session:
                session.add(client)
                session.commit()

        except Exception as error:
            logger.error(error)

    def list_clients(self):
        """
        Returns:
            Tuple of (tuple(Columns), List[tuple(Row)]) .ex. ((id, Name), [(1, John), (2, Doe)])
        """

        stmt = """SELECT * FROM "Clients" JOIN "Rates" ON "Rates".id = "Clients".rates_id """
        clients = self.execute_sql(stmt).fetchall()
        if clients:
            cols = clients[0]._asdict()
            cols.pop("rates_id")
            cols = tuple(cols.keys())
            rows = clients
            return (cols, rows)

    def edit_client(self, client_name, new_name, new_email, new_rates):
        with self.session as session:
            scalars = session.execute(
                select(ClientModel, RatesModel)
                .filter_by(name=f"{client_name}")
                .join(RatesModel)
            ).all()
            if scalars:
                client_model = scalars[0]._asdict()["ClientModel"]
                rates_model = scalars[0]._asdict()["RatesModel"]
                if new_rates:
                    normal, expedite, interpreted = new_rates
                    rates_model.normal = normal
                    rates_model.expedite = expedite
                    rates_model.interpreted = interpreted
                if new_name:
                    client_model.name = new_name
                if new_email:
                    client_model.email = new_email
                session.commit()

    def delete_client(self, client_name):
        with self.session as session:
            c = session.execute(
                select(ClientModel).filter_by(name=f"{client_name}")
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
    ):

        logger.info(f"Creating new job {job_number}")

        amount = float(job_rate) * float(quantity)
        amount = truncate(amount, 2)

        job = JobModel(
            client_id=client_id,
            date_received=date_received,
            job_number=job_number,
            job_type=job_type,
            total_quantity=total_quantity,
            job_rate=job_rate,
            amount=amount,
            quantity=quantity,
            date_due=date_due,
            job_path=job_path,
            note=note,
        )
        return job

    def save_job(self, job):
        with self.session as session:
            session.add(job)
            session.commit()

    def list_jobs(self):
        stmt = str(
            select(ClientModel.name.label("Client Name"), JobModel).join(ClientModel)
        )
        jobs = self.execute_sql(stmt).fetchall()
        if jobs:
            cols = jobs[0]._asdict()
            cols.pop("client_id")
            cols = tuple(cols.keys())
            rows = jobs
            return (cols, rows)

    def edit_job(self, **kwargs):
        new_dict = {k: v for k, v in kwargs.items() if v is not None}
        stmt = select(JobModel).filter(JobModel.id == kwargs["job_id"])

        with self.session as session:
            scalars = session.execute(stmt).all()
            jobs_model = scalars[0]._asdict()["JobModel"]

            if kwargs["client_id"]:
                stmt = (
                    select(ClientModel, RatesModel)
                    .join(RatesModel)
                    .filter(ClientModel.id == kwargs["client_id"])
                )
                try:
                    scalars = session.execute(stmt).all()
                    client_model = scalars[0]._asdict()["ClientModel"]
                    rates_model = scalars[0]._asdict()["RatesModel"]
                    new_dict["client_id"] = client_model.id
                    new_rate = rates_model.__dict__[jobs_model.job_type]
                    new_dict["job_rate"] = new_rate
                    new_dict["amount"] = truncate(new_rate * jobs_model.quantity, 2)

                except Exception as error:
                    logger.error(error)

            if kwargs.get("job_rate", "") and kwargs.get("quantity", ""):
                new_dict["job_rate"] = kwargs["job_rate"]
                new_dict["quantity"] = kwargs["quantity"]
                new_dict["amount"] = truncate(
                    kwargs["job_rate"] * kwargs["quantity"], 2
                )

            elif kwargs.get("job_rate", ""):
                new_dict["job_rate"] = kwargs["job_rate"]
                new_dict["amount"] = truncate(
                    kwargs["job_rate"] * jobs_model.quantity, 2
                )

            elif kwargs.get("quantity", ""):
                new_dict["quantity"] = kwargs["quantity"]
                new_dict["amount"] = truncate(
                    kwargs["quantity"] * jobs_model.job_rate, 2
                )

            for k, v in new_dict.items():
                jobs_model.__setattr__(f"{k}", v)

            session.commit()

    def delete_job(self, job_id):
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
