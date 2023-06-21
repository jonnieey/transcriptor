import csv
import shutil
import zipfile
from copy import copy
from datetime import date
from pathlib import Path
from typing import Callable, Optional

import yaml
from appdirs import user_config_dir, user_data_dir

from transcriptor.models import ConfigModel, ProfileModel
from transcriptor.utils import date_to_str as dts
from transcriptor.utils import (
    get_media_files,
    list_from_docx_table,
    mkdirp,
    next_non_existant_file,
    sc,
)
from transcriptor.utils import str_to_date as std
from transcriptor.utils import truncate

APP_NAME = "transcriptor4"


class BaseTranscriptor:
    """
    Base class for transcriptor
    """

    _shared_state: dict[any, any] = {}

    def __init__(self):
        self.__dict__ = self._shared_state


class Transcriptor(BaseTranscriptor):
    config_dir = user_config_dir(APP_NAME)
    config_file = Path(config_dir).joinpath("configuration.yml")
    mkdirp([config_dir])
    config_changed = False

    def __init__(self, api=None, config: dict = None):
        self.config = config if config is not None else self.load_config()

        if api is None:
            from transcriptor.api import API

            self.base_dir = Path(self.config.base_dir)
            mkdirp([self.base_dir])

            self.api = API(self.base_dir)
        else:
            self.base_dir = Path(api.base_dir)
            self.api = api

        self.date_format = self.config.date_format
        self.profile = self.load_profile()

    def load_config(self) -> ConfigModel:
        """
        Load config

        Returns:
            ConfigModel object
        """
        if self.config_file.exists():
            with open(self.config_file, "r") as fd:
                return ConfigModel(**yaml.safe_load(fd))
        else:
            config_dict = {
                "base_dir": user_data_dir(APP_NAME),
                "date_format": "%Y-%m-%d",
            }
            self.save_config(config_dict)
            return ConfigModel(**config_dict)

    def save_config(self, config_dict: dict = {}) -> None:
        """
        Save config to file

        Arguments:
            config_dict: dict of config
        """
        self.config = ConfigModel(**config_dict)
        with open(self.config_file, "w") as fd:
            self.config.save(fd)

    def save_profile(self, profile_dict: dict = {}) -> None:
        """
        Save profile

        Arguments:
            profile_dict: dict of profile
        """
        profile_file = self.base_dir.joinpath("profile.yml")
        profile = ProfileModel(**profile_dict) if profile_dict else ProfileModel()
        with open(profile_file, "w") as fd:
            profile.save(fd)
        self.profile = profile

    def load_profile(self):
        """
        Load profile

        Returns:
            ProfileModel object
        """
        profile_file = self.base_dir.joinpath("profile.yml")
        if profile_file.exists():
            try:
                with open(profile_file, "r") as fd:
                    return ProfileModel(**yaml.safe_load(fd))
            except TypeError:
                self.save_profile()
                return ProfileModel()
        else:
            self.save_profile()
            return ProfileModel()

    @property
    def profile(self):
        return self.load_profile()

    @profile.setter
    def profile(self, profile):
        if isinstance(profile, ProfileModel):
            self._profile = profile
        elif isinstance(profile, dict):
            self._profile = ProfileModel(**profile)
        else:
            raise TypeError

    def create_client(self, name: str, email: str, rates: dict = {}) -> Optional[int]:
        """
        Create a client

        Arguments:
            name: Client name
            email: Client email
            rates: Client rates dict

        Returns:
            New client ID
        """
        client_dict = {"name": name, "email": email}
        client_id = self.api.add_clients(client_dict)

        client_rates = {"normal": 0.4, "expedite": 0.6, "interpreted": 0.3}
        client_rates["client_id"] = client_id
        client_rates.update(rates)
        rates_id = self.api.add_rates(client_rates)

        client_dir = self.base_dir.joinpath("clients").joinpath(sc(name))
        mkdirp([client_dir])
        template_path = Path(__file__).parent.joinpath("templates")
        shutil.copytree(
            template_path, client_dir.joinpath("templates"), dirs_exist_ok=True
        )
        return client_id

    def create_job_dir(
        self, client_name: str, job_num: str, date_rec: str | date, date_due: str | date
    ) -> Path:
        """
        Create a job directory

        Arguments:
            client_name: Client name
            job_num: Job number
            date_rec: Date received
            date_due: Date due

        Returns:
            Job directory path object
        """
        date_rec = std(date_rec, self.date_format)
        date_due = std(date_due, self.date_format)

        job_dir = (
            self.base_dir.joinpath("clients")
            .joinpath(sc(client_name))
            .joinpath(f"{date_rec.year}")
            .joinpath(f"{date_rec.strftime('%B')}")
            .joinpath(
                f"{date_rec.strftime('%d_%a')}_{job_num}_DUE_{date_due.strftime('%d_%a')}"
            )
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
        # moved_file = shutil.move(job_file, job_dir)
        moved_file = shutil.copy(job_file, job_dir)
        if zipfile.is_zipfile(moved_file):
            zipfile.ZipFile(moved_file).extractall(job_dir)

    def get_job_template_path(self, client: str, template: str) -> Path:
        """
        Select a job template for a task

        Arguments:
            client: Client name
            template: Template name initials

        Returns:
            Path to template file
        """
        template_mapping = {
            "zd": "Zoom Deposition Block Files.doc",
            "nh": "Hearing Block Files.doc",
            "zeo": "Zoom Examination Under Oath Block Files.doc",
            "zh": "Zoom Hearing Block Files.doc",
            "zus": "Zoom Unsworn Statement Block Files.doc",
            "zwc": "Zoom Workers Comp Deposition Block Files.doc",
            "tt": "Tape Transcript.doc",
            "me": "Compulsory Medical Exam Template.doc",
            "zdi": "Zoom Deposition Block File with Interpreter.doc",
        }
        client_template_dir = self.base_dir.joinpath("clients", sc(client), "templates")

        if not client_template_dir.exists():
            jobs_templates_path = Path(__file__).parent.joinpath("templates")
            shutil.copytree(jobs_templates_path, client_template_dir)

        template_path = client_template_dir.joinpath(template_mapping[template])
        return template_path

    def create_job(
        self, job_file: str | Path, job_callback: Callable, task_callback: Callable
    ) -> None:
        """
        Create a job

        Arguments:
            job_file: Path object or path-like string to job file
            job_callback: Job callback function
            task_callback: Task callback function
        """
        job_info = job_callback(job_file)

        stmt = """
            SELECT c.name, r.normal, r.expedite, r.interpreted
            FROM clients AS c
            JOIN rates AS r ON c.id = r.client_id
            WHERE c.id = ?
        """
        client = self.api.cursor.execute(stmt, (job_info["client_id"],)).fetchone()

        if not client:
            print("No client found")
            return

        # create job directory
        client_name = client["name"]
        job_dir = self.create_job_dir(
            client_name, job_info["job_num"], job_info["date_rec"], job_info["date_due"]
        )

        rates = {
            job_type: rate
            for job_type, rate in client.items()
            if job_type in ["normal", "expedite", "interpreted"]
        }

        self.mv_extract_job_file(job_file, job_dir)
        tasks = get_media_files(job_dir)

        jobs = []

        for task in tasks:
            cb_task_info = task_callback(task)
            if not cb_task_info:
                continue
            task_info = copy(job_info)
            task_info.update(cb_task_info)

            template_path = self.get_job_template_path(
                client_name, task_info["job_template"]
            )

            job_path = next_non_existant_file(
                job_dir.joinpath(
                    "{} Due {}.doc".format(
                        job_info["job_num"],
                        job_info["date_due"].strftime("%m.%d"),
                    )
                ),
            )
            shutil.copy(template_path, job_path)

            task_info["job_rate"] = client.get(task_info["job_type"].lower())
            task_info["amount"] = truncate(
                float(task_info["job_rate"]) * float(task_info["quantity"]), 2
            )

            jobs_dict = {
                "client_id": job_info["client_id"],
                "date_received": job_info["date_rec"],
                "job_number": job_info["job_num"],
                "status": "Pending",
                "amount": task_info["amount"],
                "job_type": task_info["job_type"],
                "date_due": job_info["date_due"],
                "total_quantity": task_info["total_quantity"],
                "quantity": task_info["quantity"],
                "job_rate": client.get(task_info["job_type"].lower()),
                "job_path": str(task),
                "note": task_info["note"],
            }
            jobs.append(jobs_dict)

        if jobs:
            self.api.add_jobs(jobs)

    def extract_cutoffs_from_docx(
        self, docx_path: str | Path, cutoff_date_fmt: str = ""
    ) -> list:
        """
        Extract cutoffs from a docx file

        Arguments:
            docx_path: Path object or path-like string to docx file
            cutoff_date_fmt: Date format for cutoffs

        Returns:
            List of cutoffs
        """
        date_fmt = self.config.date_format
        raw_cutoff_list = list_from_docx_table(docx_path)

        cutoff_date_fmt = cutoff_date_fmt or "%m/%d/%Y"
        cutoffs_list = [
            [
                dts(std(cutoff, cutoff_date_fmt), date_fmt),
                dts(std(deposit, cutoff_date_fmt), date_fmt),
            ]
            for (cutoff, deposit) in raw_cutoff_list[1:]
        ]
        cutoffs_list.insert(0, raw_cutoff_list[0])
        return cutoffs_list

    def save_cutoffs(self, cutoffs_list: list) -> None:
        """
        Save cutoffs

        Arguments:
            cutoffs_list: List of cutoffs
        """
        cutoff_file = self.base_dir.joinpath("cutoffs.csv")
        with open(cutoff_file, "w") as fd:
            writer = csv.writer(fd)
            writer.writerows(cutoffs_list)

    def load_cutoffs(self, cutoffs_path: str = ""):
        """
        Load cutoffs

        Arguments:
            cutoffs_path: Path object or path-like string to cutoffs

        Returns:
            List of cutoffs
        """
        cutoff_file = cutoffs_path or self.base_dir.joinpath("cutoffs.csv")
        with open(cutoff_file, "r") as fd:
            return list(csv.reader(fd))
