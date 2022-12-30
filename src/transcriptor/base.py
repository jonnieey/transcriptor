import logging
import os
import shutil
import sys
import zipfile
from datetime import date, datetime, timedelta
from typing import Any, Callable, Dict, Optional

from appdirs import user_config_dir, user_data_dir
from jinja2 import Environment, PackageLoader, select_autoescape
from sqlalchemy import select
from weasyprint import HTML

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
    config_class = ConfigModel

    def __init__(self, config: ConfigModel = None):
        self.config = self.make_config()

        self.base_dir = Path(self.config.base_dir)
        mkdirp([self.base_dir])
        self.api = API(self.base_dir)

        self.clients_dir = self.base_dir.joinpath("clients")
        mkdirp([self.clients_dir])

    def make_config(self):
        DEFAULT_BASE_DIR = user_data_dir(appname="transcriptor3")
        DEFAULT_CONFIG = {"date_format": "%Y-%m-%d", "base_dir": f"{DEFAULT_BASE_DIR}"}
        config = self.config_class(**DEFAULT_CONFIG)
        env = os.environ.get("TRANS_ENV", "")
        if env:
            config.from_env(env)
        return config

    @staticmethod
    def default_config() -> ConfigModel:
        """
        Generate default configuration file.

        Returns:
            ConfigModel object
        """
        logger.info("Create default configuration")
        date_format = "%Y-%m-%d"
        base_dir = user_data_dir(appname="transcriptor3")
        config_obj = ConfigModel(date_format=date_format, base_dir=base_dir)
        return config_obj

    # TODO refactor to specify config file
    # def get_config(self) -> ConfigModel:
    #     """
    #     Load configuration from file.
    #
    #     Returns:
    #         ConfigModel object
    #     """
    # CONFIG_DIR = Path(user_config_dir(appname=APP_NAME))
    # CONFIG_FILE = CONFIG_DIR.joinpath("config.yml")
    #
    # def save_default():
    #     config = self.default_config()
    #     self.add_config(config)
    #     return config
    #
    # if not CONFIG_FILE.exists():
    #     touch([CONFIG_FILE])
    #     save_default()
    #
    # with open(CONFIG_FILE, "r") as fd:
    #     try:
    #         obj_dict = yaml.safe_load(fd)
    #         if obj_dict is None:
    #             save_default()
    #         obj = ConfigModel(**obj_dict)
    #         return obj
    #     except TypeError as error:
    #         logger.error(error)
    #         sys.exit(1)
    # return ConfigModel()

    def add_config(self, config: ConfigModel) -> None:
        """
        Save configuration to default config file.

        Arguments:
            config: ConfigModel object
        """

        CONFIG_FILE = Path(user_config_dir(appname=APP_NAME)).joinpath("config.yml")
        touch([CONFIG_FILE])
        with open(CONFIG_FILE, "w") as fd:
            config.save(fd)

    def get_profile(self) -> object | ProfileModel:
        """
        Load profile from file.

        Returns:
            ProfileModel object
        """
        PROFILE_FILE = self.base_dir.joinpath("profile.yml")

        if not PROFILE_FILE.exists():
            touch([PROFILE_FILE])

        with open(PROFILE_FILE, "r+") as fd:
            return self.api.load_profile(fd)

    def add_profile(self, profile: ProfileModel) -> None:
        """
        Save profile object to default profile file.

        Arguments:
            profile: ProfileModel object
        """
        PROFILE_FILE = self.base_dir.joinpath("profile.yml")
        with open(PROFILE_FILE, "w") as fd:
            profile.save(fd)

    @property
    def profile(self) -> object | ProfileModel:
        return self.get_profile()

    def create_job_dir(
        self, client_name: str, job_num: str, date_r: str, date_due: str
    ) -> Path:
        """
        Create job directory.

        Arguments:
            client_name: Name of client
            job_num: Job number
            date_r: Date received
            date_due: Date due

        Returns:
            Path object
        """
        job_dir = (
            self.base_dir.joinpath("clients")
            .joinpath(sc(client_name))
            .joinpath(str(date.today().year))
            .joinpath(f"{date_r}_{job_num}_DUE-{date_due}")
        )
        mkdirp([job_dir])
        return job_dir

    @staticmethod
    def mv_extract_job_file(job_file: str | Path, job_dir: str | Path) -> None:
        """
        Move/Extract job file to jobs directory

        Arguments:
            job_file: Path object or path-like string to job file
            job_dir: Path object or path-like string to job directory
        """
        # TODO move file
        moved_file = shutil.copy(job_file, job_dir)
        if zipfile.is_zipfile(moved_file):
            zipfile.ZipFile(moved_file).extractall(job_dir)

    def add_client(self, name: str, email: str) -> None:
        new_client = self.api.create_client(name, email)
        self.api.save_client(new_client)
        CLIENT_DIR = self.base_dir.joinpath("clients").joinpath(sc(name))
        mkdirp([CLIENT_DIR])

    def add_job(
        self,
        add_job_cb: Callable[
            [str, ClientModel, RatesModel, str, str, str | Path], JobModel
        ],
        client_name: str,
        job_file: str | Path,
        date_received: str = "",
        date_due: str = "",
    ) -> None:
        """
        Add job to database

        Arguments
        add_job_cb: Job callback function. Function that gets job info.
        client_name: Client's name
        job_file: Job file
        date_received: Date received
        date_due: Date due

        """

        job_num = parse_job_number(str(job_file))

        with self.api.session as session:
            stmt = (
                select(ClientModel, RatesModel)
                .filter(ClientModel.name.like(f"%{client_name}%"))
                .join(RatesModel)
            )
            scalars = session.execute(stmt).all()
            # TODO Handle multiple clients with almost same name
            # Only one client found
            if len(scalars) == 1:
                client = scalars[0]._asdict()["ClientModel"]
                rates = scalars[0]._asdict()["RatesModel"]

                job_dir = self.create_job_dir(
                    client.name, job_num, date_received, date_due
                )
                self.mv_extract_job_file(job_file, job_dir)

                media_files = get_media_files(job_dir)
                for media_file in media_files:
                    # callback return JobModel object

                    job = add_job_cb(
                        str(media_file),
                        client,
                        rates,
                        date_received,
                        job_num,
                        job_dir,
                    )
                    self.api.save_job(job)

    def create_invoice(self, client_id, period_start, period_end):
        # client, jobs, totals =
        INVOICE_COUNTER_FILE = self.base_dir.joinpath("invoice_counter.txt")
        touch([INVOICE_COUNTER_FILE])
        with open(INVOICE_COUNTER_FILE, "r") as fd:
            count = fd.readline()
            invoice_counter = 0 if count == "" else int(count)

        client, jobs_list, (amount, amount_paid) = self.api.create_invoice_data(
            client_id, period_start, period_end
        )
        profile = self.get_profile().__dict__
        DATE_FMT = self.config.date_format

        created = datetime.today()
        due = created + timedelta(days=7)

        context = {
            "client": client,
            "jobs": jobs_list,
            "amount": amount,
            "profile": profile,
            "data": {
                "created": created.strftime(DATE_FMT),
                "due": due.strftime(DATE_FMT),
                "invoice_number": f"{invoice_counter + 1:05}",
            },
        }
        env = Environment(
            loader=PackageLoader("transcriptor", "invoice_templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )
        template_file = "invoice.html"
        template = env.get_template(template_file)
        output_text = template.render(context)
        HTML(string=output_text).write_pdf("test.pdf")

        with open(INVOICE_COUNTER_FILE, "w") as fd:
            fd.write(f"{invoice_counter + 1:05}")


if __name__ == "__main__":
    app = Transcriptor()
    app.create_invoice(2, "2022-01-12", "2022-12-30")
