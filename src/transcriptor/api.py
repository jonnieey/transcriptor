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
    def load_config(self, app_name="transcriptor3"):
        config_path = Path(user_config_dir(app_name))
        config_file = config_path.joinpath("config.yml")
        logger.info("Load config.")

        if not config_file.exists():
            try:
                touch(config_file)
                config = self.default_config()
                with open(config_file, "w") as fd:
                    logger.info(f"Writing default configuration to {config_file}")
                    config.save(fd)
                return config

            except Exception as error:
                logger.info(f"Unable to write new configuration file.")
                logger.error(error)

        else:
            with open(config_file, "r") as fd:
                try:
                    config_dict = yaml.safe_load(fd)
                    config = ConfigModel(**config_dict)
                    return config
                except yaml.YAMLError as error:
                    logger.info(f"Unable to read configuration file.")
                    logger.error(error)

    def default_config(self):
        logger.info("Create default configuration")
        date_format = "%Y-%m-%d"
        base_dir = Path(user_data_dir(appname="transcriptor3"))
        config_obj = ConfigModel(date_format=date_format, base_dir=base_dir)
        return config_obj

    def load_profile(self, app_name="transcriptor3", BASE_DIR=None):
        logger.info("Load Profile")

        base_dir = (
            Path(user_data_dir(appname=app_name))
            if BASE_DIR == None
            else Path(BASE_DIR)
        )
        profile_file = base_dir.joinpath("profile.yml")
        if not profile_file.exists():
            try:
                touch(profile_file)
                profile = ProfileModel()
                with open(profile_file, "w") as fd:
                    logger.info(f"Writing default profile to {profile_file}")
                    profile.save(fd)
                return profile

            except Exception as error:
                logger.info(f"Unable to write new profile file.")
                logger.error(error)

        else:
            with open(profile_file, "r") as fd:
                try:
                    profile_dict = yaml.safe_load(fd)
                    profile = ProfileModel(**profile_dict)
                    return profile
                except yaml.YAMLError as error:
                    logger.info(f"Unable to read profile file.")
                    logger.error(error)

    def create_client(self, name: str, email: str, rates: dict):
        client_uuid = str(uuid.uuid4())
        logger.info(f"Creating new client {name}")
        client = ClientModel(client_id=client_uuid, name=name, email=email, rates=rates)
        return client

    def save_client(self, client: ClientModel, app_name="transcriptor3", BASE_DIR=None):

        base_dir = (
            Path(user_data_dir(appname=app_name))
            if BASE_DIR == None
            else Path(BASE_DIR)
        )
        client_file = (
            base_dir.joinpath("clients")
            .joinpath(sc(client.name))
            .joinpath(f"{client.name}.yml")
        )
        if not client_file.exists():
            touch(client_file)

        logger.info(f"Saving client {client.name}")

        with open(client_file, "w") as fd:
            client.save(fd)

    def get_client_from_uuid(self, uuid: str, app_name="transcriptor3", BASE_DIR=None):

        base_dir = (
            Path(user_data_dir(appname=app_name))
            if BASE_DIR == None
            else Path(BASE_DIR)
        )

        logger.info("Get client from uuid")

        for client_dir in base_dir.joinpath("clients").iterdir():
            client_file = client_dir.joinpath(f"{client_dir.name}.yml")
            if client_file.exists():
                try:
                    with open(client_file, "r") as fd:
                        client = yaml.safe_load(fd)
                        if client["client_id"] == uuid:
                            return ClientModel(**client)
                except Exception as error:
                    logger.error(error)
        return None

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

        job_uuid = str(uuid.uuid4())
        logger.info(f"Creating new job {job_number}")

        job = JobModel(
            job_id=job_uuid,
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

    def save_job(self, job: JobModel, app_name="transcriptor3", BASE_DIR=None):
        base_dir = (
            Path(user_data_dir(appname=app_name))
            if BASE_DIR == None
            else Path(BASE_DIR)
        )
        client = self.get_client_from_uuid(job.client_id)
        client_jobs_file = (
            base_dir.joinpath("clients").joinpath(sc(client.name)).joinpath("jobs.yml")
        )
        if not client_jobs_file.exists():
            touch(client_jobs_file)
        logger.info("Save Job")
        with open(client_jobs_file, "r+") as fd:
            job.save(fd)


if __name__ == "__main__":
    name = "Client"
    email = "clientemail@gmail.com"
    rates = {"Normal": 0.4, "Expedite": 0.5, "Interpreted": 0.3}
    api = API()
    client = api.create_client(name, email, rates)
    api.save_client(client)
    # print(api.get_client_from_uuid(client.client_id))
    job = api.create_job(
        client_id=client.client_id,
        date_received="2022-05-05",
        job_number="56321",
        job_type="Normal",
        total_quantity="42.12630",
        job_rate="0.40",
        quantity="21.06315",
        date_due="2022-06-01",
        job_path="somerandompath",
    )
    api.save_job(job)
    # print(yaml.dump(dict(job)))
    # # api.create_client(name="john", email="johnjahi@tmgil.com", rates={"Normal": 0.45, "Expedite": 0.60, "Interpreted": 0.3})
    #
    #
