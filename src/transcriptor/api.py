import io
import logging
import sys
import uuid
from pathlib import Path

import yaml
from appdirs import user_config_dir, user_data_dir

from transcriptor.models import *
from transcriptor.utils import *

logger = logging.getLogger(__name__)


class API:
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

    def load_config(self, obj, file_object):
        logger.info("Load config")
        config = self.load_object(obj, file_object)
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

    def load_profile(self, obj, file_object):
        logger.info("Load profile")
        profile = self.load_object(obj, file_object)
        return profile

    def create_client(self, name: str, email: str, rates: dict):
        client_id = str(uuid.uuid4())
        logger.info(f'Creating new client "{name}"')
        client = ClientModel(client_id=client_id, name=name, email=email, rates=rates)
        return client

    def save_client(self, obj, file_object):
        logger.info(f'Saving client "{obj.name}"')
        client = self.save_object(obj, file_object)
        return client

    def load_client(self, obj, file_object):
        logger.info(f'Loading client "{obj.name}"')
        client = self.load_object(obj, file_object)
        return client

    def get_clients(self, clients_dir: Path):
        logger.info("Get all clients")
        clients_dir = Path(clients_dir)

        for client_dir in clients_dir.iterdir():
            client_file = client_dir.joinpath(f"{client_dir.name}.yml")
            if client_file.exists():
                try:
                    with open(client_file, "r") as fd:
                        client = self.load_object(ClientModel, fd)
                        yield client

                except Exception as error:
                    logger.error(error)

    def get_client_by_attr(self, attr, attr_value, clients_dir: Path):
        logger.info("Get client attribute")
        clients_dir = Path(clients_dir)

        for client_dir in clients_dir.iterdir():
            client_file = client_dir.joinpath(f"{client_dir.name}.yml")
            if client_file.exists():
                try:
                    with open(client_file, "r") as fd:
                        client = self.load_object(ClientModel, fd)
                        if attr_value in client.get(attr):
                            yield client

                except Exception as error:
                    logger.error(error)

    def create_job(
        self,
        client_id: str,
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

        job_id = str(uuid.uuid4())
        logger.info(f"Creating new job {job_number}")

        job = JobModel(
            job_id=job_id,
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

    def save_job(self, obj, file_object):
        logger.info(f'Saving job "{obj.job_id}"')
        job = self.save_object(obj, file_object)
        return job


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
    name = "Client"
    email = "clientemail@gmail.com"
    rates = {"Normal": 0.4, "Expedite": 0.5, "Interpreted": 0.3}
    client = api.create_client(name, email, rates)
    client_file = (
        base_dir.joinpath("clients").joinpath(sc(name)).joinpath(f"{sc(name)}.yml")
    )
    # if not client_file.exists():
    #     touch(client_file)
    #
    # api.save_client(client, client_file.open(mode="w"))
    # # # print(api.get_client_from_uuid(client.client_id))
    # job = api.create_job(
    #     client_id=client.client_id,
    #     date_received="2022-05-05",
    #     job_number="56321",
    #     job_type="Normal",
    #     total_quantity="42.12630",
    #     job_rate="0.40",
    #     quantity="21.06315",
    #     date_due="2022-06-01",
    #     job_path="somerandompath",
    # )
    # job_file = base_dir.joinpath("clients").joinpath(sc(client.name)).joinpath(f"jobs-2022.yml")
    # if not job_file.exists():
    #     touch(job_file)
    # api.save_job(job, job_file.open("r+"))
    # print(api.get_client_from_uuid("126e297e-54cb-46fb-9325-a7ea31ace10e", base_dir.joinpath("clients")))
    # print(yaml.dump(dict(job)))
    # # api.create_client(name="john", email="johnjahi@tmgil.com", rates={"Normal": 0.45, "Expedite": 0.60, "Interpreted": 0.3})
    #
    #
