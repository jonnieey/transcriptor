import logging
import os
import shutil
import zipfile
from datetime import date, datetime, timedelta
from typing import Any, Callable, Dict

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
        self.config = config if config is not None else self.make_config()

        self.base_dir = Path(self.config.base_dir)
        mkdirp([self.base_dir])
        self.api = API(self.base_dir)

        self.profile_file = self.base_dir.joinpath("profile.yml")
        self.make_profile()

        self.clients_dir = self.base_dir.joinpath("clients")
        mkdirp([self.clients_dir])

    def make_config(self):
        DEFAULT_BASE_DIR = Path(user_data_dir(appname=APP_NAME))
        DEFAULT_CONFIG = {"date_format": "%Y-%m-%d", "base_dir": f"{DEFAULT_BASE_DIR}"}
        DEFAULT_CONFIG_DIR = Path(user_config_dir(appname=APP_NAME))
        self.config_file = DEFAULT_CONFIG_DIR.joinpath("config.yml")

        config = self.config_class(**DEFAULT_CONFIG)
        config.from_file(self.config_file)

        env = os.environ.get("TRANS_ENV", "")
        if env:
            config.from_env(env)
        return config

    def save_config(self):
        with open(self.config_file, "w") as fd:
            self.config.save(fd)

    def save_profile(self):
        with open(self.profile_file, "w") as fd:
            self.profile.save(fd)

    def make_profile(self):
        """
        Load profile from file.

        Returns:
            ProfileModel object
        """

        if not self.profile_file.exists():
            touch([self.profile_file])

        with open(self.profile_file, "r+") as fd:
            self.profile = self.api.load_profile(fd)

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
        DATE_FMT = self.config.date_format
        date_r = str_to_date(date_r, DATE_FMT).strftime("%d_%a")
        date_due = str_to_date(date_due, DATE_FMT).strftime("%d_%a")

        job_dir = (
            self.base_dir.joinpath("clients")
            .joinpath(sc(client_name))
            .joinpath(str(date.today().year))
            .joinpath(str(date.today().strftime("%B")))
            .joinpath(f"{date_r}_{job_num}_DUE_{date_due}")
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

    def select_job_template(self, template_init: str):
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
        template_path = (
            Path(__file__)
            .parent.joinpath("templates")
            .joinpath(template_mapping[template_init])
        )

        return template_path

    def next_non_existant_file(self, filename):
        base_dir = str(Path(filename).parent.absolute())
        nf = filename
        root, ext = Path(nf).stem, Path(nf).suffix
        i = 0
        while Path(nf).exists():
            i += 1
            nf = f"{base_dir}/{root}_{i}{ext}"
        return Path(nf)

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
        DATE_FMT = self.config.date_format

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

                    job, job_temp_init = add_job_cb(
                        str(media_file),
                        client,
                        rates,
                        date_received,
                        job_num,
                        job_dir,
                    )
                    job_template = self.select_job_template(job_temp_init)
                    # TODO Copy numbered files for each task
                    job_path = self.next_non_existant_file(
                        job_dir.joinpath(
                            f"{job_num} Due {str_to_date(date_due, DATE_FMT).strftime('%m.%d')}.doc",
                        ),
                    )
                    shutil.copy(job_template, job_path)

                    self.api.save_job(job)

    def create_invoice(self, client_id, period_start, period_end):
        # client, jobs, totals =
        client, jobs_list, (amount, amount_paid) = self.api.create_invoice_data(
            client_id, period_start, period_end
        )

        CLIENT_DIR = self.base_dir.joinpath("clients").joinpath(sc(client["name"]))
        INVOICES_DIR = CLIENT_DIR.joinpath("invoices")
        INVOICE_COUNTER_FILE = INVOICES_DIR.joinpath("invoice_counter.txt")
        touch([INVOICE_COUNTER_FILE])

        with open(INVOICE_COUNTER_FILE, "r") as fd:
            count = fd.readline()
            invoice_counter = 0 if count == "" else int(count)

        profile = self.profile.__dict__
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

        invoice_file_name = f"{created.strftime(DATE_FMT)}_{client['name']}_invoice"
        html_invoice_file_name = f"{invoice_file_name}.html"
        pdf_invoice_file_name = f"{invoice_file_name}.pdf"

        with open(INVOICES_DIR.joinpath(html_invoice_file_name), "w") as fd:
            fd.write(output_text)

        invoice_file = str(INVOICES_DIR.joinpath(pdf_invoice_file_name))
        HTML(string=output_text).write_pdf(invoice_file)

        with open(INVOICE_COUNTER_FILE, "w") as fd:
            fd.write(f"{invoice_counter + 1:05}")


if __name__ == "__main__":
    app = Transcriptor()
    print(app.config)
    # t(app.select_job_template("zd"))
