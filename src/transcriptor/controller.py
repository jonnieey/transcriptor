import logging
from pathlib import Path

import yaml
from sqlalchemy import text
from sqlalchemy.orm import Session

from transcriptor.database import Base, Database
from transcriptor.models import ClientModel, JobModel, ProfileModel, RatesModel
from transcriptor.utils import *
from transcriptor.view import *

logger = logging.getLogger(__name__)


class API:
    def __init__(self, base_dir, db_path="transcriptor.db"):

        self.base_dir = Path(base_dir)
        mkdirp([self.base_dir])

        self.db = Database(self.base_dir.joinpath(db_path))
        Base.metadata.create_all(self.db.engine)

    def save_object(self, obj, file_object):
        obj.save(file_object)
        return obj

    def load_object(self, obj, file_object):
        obj_dict = yaml.safe_load(file_object)
        if obj_dict is None:
            return obj()
        obj = obj(**obj_dict)
        return obj

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
            with Session(self.db.engine) as session:
                session.add(client)
                session.commit()

        except Exception as error:
            logger.error(error)

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

        job = JobModel(
            client_id=client_id,
            date_received=date_received,
            job_number=job_number,
            job_type=job_type,
            total_quantity=total_quantity,
            job_rate=job_rate,
            quantity=quantity,
            date_due=date_due,
            job_path=job_path,
            note=note,
        )
        return job

    def save_job(self, job):
        with Session(self.db.engine) as session:
            session.add(job)
            session.commit()

    def execute_sql(self, s):
        stmt = text(s)
        with Session(self.db.engine) as session:
            return session.execute(stmt)


if __name__ == "__main__":
    base_dir = Path(user_data_dir(appname="transcriptor3"))
    api = API()

    # fname = "John"
    # lname = "Njahi"
    # area = "Nairobi"
    # country = "Kenya"
    #
    # profile = ProfileModel(fname, lname, area, country)
    # profile_path = base_dir.joinpath("profile.yml")
    # if not profile_path.exists():
    #     touch(profile_path)
    # api.save_profile(profile, profile_path.open("w"))
    #
    #
    # for i in range(3):
    #     name = f"Client{i}"
    #     email = f"client{i}email@gmail.com"
    #     rates = {"normal": 0.4, "expedite": 0.5, "interpreted": 0.3}
    #     client = api.create_client(name, email, rates)
    # # print(api.create_job_dir("john", "222222", "2022", "11-10", "11-15"))
    #
    # stmt = select(ClientModel).where(ClientModel.name == "Client1")
    # for client in api.db.session.scalars(stmt):
    #     print(client.name)
    #     print(r.all())
    #     r = session.execute(text("select * from Rates"))
    #     print(r.all())
    # client.save()
    # clients = api.query.get_clients_by_attr("client_id", 1)
    # from pprint import pprint
    # clients_test = clients.fetchall()
    # print(clients_test)
    # if not client_file.exists():
    #     touch(client_file)
    #
    # api.save_client(client, client_file.open(mode="w"))
    # # # print(api.get_client_from_uuid(client.client_id))
    # for i in range(3):
    #     job = api.create_job(
    #         client_id=i,
    #         date_received="2022-05-05",
    #         job_number="56321",
    #         job_type="Normal",
    #         total_quantity="42.12630",
    #         job_rate="0.40",
    #         quantity="21.06315",
    #         date_due="2022-06-01",
    #         job_path="somerandompath",
    #     )
    # # r = session.execute(text("select * from Jobs"))
    # # print(r.all())
    # from pprint import pprint
    #
    # with api.db.session as session:
    #     r = session.execute(
    #         text("select * from Jobs JOIN Clients WHERE Clients.name = 'Client2'")
    #     )
    #     pprint(r.all())
    # # job.save()
    # jobs = api.query.get_job_by_attr()
    # print(json.dumps(jobs.fetchone()))
    # job_file = base_dir.joinpath("clients").joinpath(sc(client.name)).joinpath(f"jobs-2022.yml")
    # if not job_file.exists():
    #     touch(job_file)
    # api.save_job(job, job_file.open("r+"))
    # print(api.get_client_from_uuid("126e297e-54cb-46fb-9325-a7ea31ace10e", base_dir.joinpath("clients")))
    # print(yaml.dump(dict(job)))
    # # api.create_client(name="john", email="johnjahi@tmgil.com", rates={"Normal": 0.45, "Expedite": 0.60, "Interpreted": 0.3})
    #
    #
    # job_file = "/home/kamikaze/Documents/Wera/Transcription2/work/Natalie Puelles/2022-11-06-585372_DUE_2022-11-11/585372 TT.zip"
    # j = api.create_job_dir("Client1", "222222", "2022", "11-10", "11-15", job_file)
