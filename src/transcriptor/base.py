import logging
import shutil
import sys
import zipfile
from datetime import date
from typing import Any, Dict

from appdirs import user_config_dir, user_data_dir

from transcriptor.controller import API
from transcriptor.models import *
from transcriptor.utils import *

logger = logging.getLogger(__name__)


class BaseTranscriptor:
    _shared_state: Dict[Any, Any] = {}

    def __init__(self):
        self.__dict__ = self._shared_state


class Transcriptor(BaseTranscriptor):
    APP_NAME = "transcriptor3"

    def __init__(self, config=None):

        self.config = config if config is not None else self.get_config()
        self.base_dir = Path(self.config.base_dir)
        mkdirp([self.base_dir])

        self.api = API(self.base_dir)

        self.clients_dir = self.base_dir.joinpath("clients")
        mkdirp([self.clients_dir])

    @staticmethod
    def default_config():
        logger.info("Create default configuration")
        date_format = "%Y-%m-%d"
        base_dir = user_data_dir(appname="transcriptor3")
        config_obj = ConfigModel(date_format=date_format, base_dir=base_dir)
        return config_obj

    def get_config(self):
        CONFIG_DIR = Path(user_config_dir(appname=self.APP_NAME))
        CONFIG_FILE = CONFIG_DIR.joinpath("config.yml")

        if not CONFIG_FILE.exists() or (yaml.safe_load(CONFIG_FILE.open("r")) is None):
            touch([CONFIG_FILE])
            config = self.default_config()
            self.add_config(config)
            return config

        with open(CONFIG_FILE, "r") as fd:
            try:
                obj_dict = yaml.safe_load(fd)
                obj = ConfigModel(**obj_dict)
                return obj
            except TypeError as error:
                logger.error(error)
                sys.exit(1)

    def add_config(self, config: ConfigModel):
        CONFIG_FILE = Path(user_config_dir(appname=self.APP_NAME)).joinpath(
            "config.yml"
        )
        touch([CONFIG_FILE])
        with open(CONFIG_FILE, "w") as fd:
            config.save(fd)

    def get_profile(self):
        PROFILE_FILE = self.base_dir.joinpath("profile.yml")

        if not PROFILE_FILE.exists() or (
            yaml.safe_load(PROFILE_FILE.open("r")) is None
        ):
            touch([PROFILE_FILE])
            profile = ProfileModel()
            self.add_profile(profile)
            return profile

        with open(PROFILE_FILE, "r") as fd:
            return self.api.load_profile(fd)

    def add_profile(self, profile: ProfileModel):
        PROFILE_FILE = self.base_dir.joinpath("profile.yml")
        with open(PROFILE_FILE, "w") as fd:
            profile.save(fd)

    @property
    def profile(self):
        return self.get_profile()

    def create_job_dir(self, client_name, job_num, date_r, date_due):
        job_dir = (
            self.base_dir.joinpath("clients")
            .joinpath(sc(client_name))
            .joinpath(str(date.today().year))
            .joinpath(f"{date_r}_{job_num}_DUE-{date_due}")
        )
        mkdirp([job_dir])
        return job_dir

    def mv_extract_job_file(self, job_file, job_dir):
        moved_file = shutil.copy(job_file, job_dir)
        if zipfile.is_zipfile(moved_file):
            zipfile.ZipFile(moved_file).extractall(job_dir)

    def add_job(self, client, job_file):
        job_num = parse_job_number(job_file)
        date_due = parse_due_date("DUE 11.19")
        today = str(date.today().strftime("%m-%d"))

        job_dir = self.create_job_dir(client.name, job_num, today, date_due)
        self.mv_extract_job_file(job_file, job_dir)

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
                    "client_id": client.id,
                    "date_received": str(date.today()),
                    "job_number": job_num,
                    "job_type": job_type,
                    "total_quantity": total_quantity,
                    "job_rate": 0.4,
                    "quantity": quantity,
                    "date_due": "2022-11-25",
                    "job_path": str(job_dir),
                    "note": note,
                }
                job = self.api.create_job(**job_dict)
                self.api.save_job(job)


if __name__ == "__main__":
    # shutil.rmtree("/home/kamikaze/.local/share/transcriptor3", ignore_errors=True)
    app = Transcriptor()
    print(app.get_config())
    print(app.get_profile())
    # app.base_dir
    # create Profile
    # app.get_profile()
    name = "John"
    email = "Johnnjahi@gmail.com"
    client = app.api.create_client(name, email)
    app.api.save_client(client)
    cl_stmt = "SELECT * from Clients WHERE name = 'John'"
    client = app.api.execute_sql(cl_stmt).first()

    job = app.api.create_job(
        client_id=client.id,
        date_received="2022-05-05",
        job_number="56321",
        job_type="Normal",
        total_quantity="42.12630",
        job_rate="0.40",
        quantity="21.06315",
        date_due="2022-06-01",
        job_path="somerandompath",
    )
    # print(job.job_number)
    # year = str(date.today().year)
    # job_dir = app.create_job_dir(name, job.job_number, year, job.date_received, job.date_due)
    job_file = "/home/kamikaze/Documents/Wera/Transcription2/work/Natalie Puelles/2022-11-14-587103_DUE_2022-11-19/587103 TT.zip"
    # app.mv_extract_job_file(job_file, job_dir)
    app.add_job(client, job_file)
