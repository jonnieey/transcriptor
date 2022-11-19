import logging
import shutil
import zipfile
from pathlib import Path

import yaml
from appdirs import user_config_dir, user_data_dir
from sqlalchemy import select, text

from transcriptor.database import Base, Database
from transcriptor.models import ClientModel, JobModel, ProfileModel, RatesModel
from transcriptor.utils import *
from transcriptor.view import *

logger = logging.getLogger(__name__)


class API:
    def __init__(self, config=None, profile=None, db_path="transcriptor.db"):
        if config is None:
            self.config = self.load_config()
        else:
            self.config = config

        self.base_dir = Path(self.config.base_dir)
        mkdirp([self.base_dir])
        self.date_format = self.config.date_format

        if profile is None:
            self.profile = self.load_profile()

        self.db = Database(self.base_dir.joinpath(db_path))
        self.init_db()

    def init_db(self):
        Base.metadata.create_all(self.db.engine)

    def save_object(self, obj, file_object):
        obj.save(file_object)
        return obj

    def load_object(self, obj, file_object):
        obj_dict = yaml.safe_load(file_object)
        obj = obj(**obj_dict)
        return obj

    def save_config(self, obj, file_object):
        logger.info("Save config")
        config = self.save_object(obj, file_object)
        return config

    def load_config(self):
        logger.info("Load config")
        config_file = Path(user_config_dir(appname="transcriptor3")).joinpath(
            "config.yml"
        )
        touch([config_file])
        try:
            with open(config_file, "r") as fd:
                obj_dict = yaml.safe_load(fd)
                if obj_dict is None:
                    raise FileNotFoundError
                config = ConfigModel(**obj_dict)
        except (FileNotFoundError) as error:
            with open(config_file, "w") as fd:
                config = self.default_config()
                config.save(fd)
        return config

    def default_config(self):
        logger.info("Create default configuration")
        date_format = "%Y-%m-%d"
        base_dir = user_data_dir(appname="transcriptor3")
        config_obj = ConfigModel(date_format=date_format, base_dir=base_dir)
        return config_obj

    def save_profile(self, obj, file_object):
        logger.info("Save profile")
        profile = self.save_object(obj, file_object)
        return profile

    def load_profile(self):
        logger.info("Load profile")
        profile_file = self.base_dir.joinpath("profile.yml")
        touch([profile_file])
        try:
            with open(profile_file, "r") as fd:
                obj_dict = yaml.safe_load(fd)
                if obj_dict is None:
                    raise FileNotFoundError
                profile = ProfileModel(**obj_dict)
        except (FileNotFoundError) as error:
            with open(profile_file, "w") as fd:
                profile = ProfileModel()
                profile.save(fd)
        return profile

    def create_client(self, name: str, email: str, rates: dict):
        logger.info(f'Creating client "{name}"')
        rate_obj = RatesModel(**rates)
        client = ClientModel(name=name, email=email, rates=rate_obj)
        client_dir = self.base_dir.joinpath("clients").joinpath(sc(name))
        client_info = client_dir.joinpath(f"{sc(name)}_info.yml")

        try:
            with self.db.session as session:
                session.add(client)
                session.commit()
                mkdirp([client_dir])
                with open(client_info, "w") as fd:
                    yaml.dump({"name": name, "email": email, "rates": rates}, fd)

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

    def create_job_dir(
        self, client_name, job_number, year, date_received, date_due, job_file
    ):
        with self.db.session as session:
            stmt = select(ClientModel).where(ClientModel.name == client_name)
            client = session.execute(stmt).first()

            job_dir = (
                self.base_dir.joinpath("clients")
                .joinpath(sc(client_name))
                .joinpath("jobs")
                .joinpath(year)
                .joinpath(f"{date_received}_{job_number}_DUE-{date_due}")
            )
            mkdirp([job_dir])
            moved_file = shutil.copy(job_file, job_dir)
            if zipfile.is_zipfile(moved_file):
                zipfile.ZipFile(moved_file).extractall(job_dir)

            # getaudio files
            media_files = get_media_files(job_dir)
            for media_file in media_files:
                do = input("Do work? [Y/N]: ")
                if do.upper() == "Y":

                    total_quantity = get_media_duration(media_file)
                    quantity = input("duration: ")
                    job_type = input("Job type: ")
                    job_template = input("Job template: ")
                    note = input("Notes: ")

                    job_dict = {
                        "client_id": client[0].id,
                        "date_received": date_received,
                        "job_number": job_number,
                        "job_type": job_type,
                        "total_quantity": total_quantity,
                        "job_rate": 0.4,
                        "quantity": quantity,
                        "date_due": date_due,
                        "job_path": str(job_dir),
                        "note": note,
                    }
                    job = self.create_job(**job_dict)
                    session.add(job)
            session.commit()

        # with self.db.session as session:
        #     session.add(job)
        #     session.commit()


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
