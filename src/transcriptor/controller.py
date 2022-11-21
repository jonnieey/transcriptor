import logging
from pathlib import Path

import yaml
from sqlalchemy import text
from sqlalchemy.orm import Session

from transcriptor.database import Base, Database
from transcriptor.models import (
    ClientModel,
    ConfigModel,
    JobModel,
    ProfileModel,
    RatesModel,
)
from transcriptor.utils import *
from transcriptor.view import *

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

    # def edit_client()

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

    def execute_sql(self, s):
        stmt = text(s)
        with self.session as session:
            return session.execute(stmt)
