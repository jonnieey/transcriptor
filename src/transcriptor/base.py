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

APP_NAME = "transcriptor3"


class BaseTranscriptor:
    _shared_state: Dict[Any, Any] = {}

    def __init__(self):
        self.__dict__ = self._shared_state


class Transcriptor(BaseTranscriptor):
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
        CONFIG_DIR = Path(user_config_dir(appname=APP_NAME))
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
        CONFIG_FILE = Path(user_config_dir(appname=APP_NAME)).joinpath("config.yml")
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

    @staticmethod
    def mv_extract_job_file(job_file, job_dir):
        # TODO move file
        moved_file = shutil.copy(job_file, job_dir)
        if zipfile.is_zipfile(moved_file):
            zipfile.ZipFile(moved_file).extractall(job_dir)

    def add_job(
        self, add_job_cb, client, rates, job_file, date_received="", date_due=""
    ):
        job_num = parse_job_number(job_file)

        job_dir = self.create_job_dir(client.name, job_num, date_received, date_due)
        self.mv_extract_job_file(job_file, job_dir)

        media_files = get_media_files(job_dir)
        for media_file in media_files:
            # callback return JobModel object

            job = add_job_cb(
                media_file=media_file,
                client=client,
                rates=rates,
                date_received=date_received,
                job_num=job_num,
                job_dir=job_dir,
            )
            self.api.save_job(job)
