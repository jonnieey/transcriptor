import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional, Union

import click
import jinja2
import pdfkit
from docxtpl import DocxTemplate

from transcriptor.client import Client
from transcriptor.client_list import ClientList, ClientLists
from transcriptor.conf import get_config
from transcriptor.job import Job
from transcriptor.profile import Profile
from transcriptor.settings import Settings
from transcriptor.utils import string_to_date

CONFIG_FOLDER = get_config()["config_folder"]


def default_settings() -> Settings:
    settings = Settings(**get_config())
    return settings


def get_settings(config_file: Path) -> dict:
    settings = Settings().load(config_file)
    return settings.__dict__ if settings else default_settings().__dict__


try:
    settings = Settings().load(CONFIG_FOLDER / "conf.json")
except FileNotFoundError:
    settings = default_settings()

CONFIG_FOLDER, JOBS_FOLDER, CLIENTS_FOLDER, DATE_FMT, INVOICES_FOLDER = (
    settings.config_folder,
    settings.jobs_folder,
    settings.clients_folder,
    settings.date_fmt,
    settings.invoices_folder,
)


def get_profile(profile_file: Path = CONFIG_FOLDER / "profile.json") -> dict:
    try:
        profile = Profile.load(profile_file)
    except FileNotFoundError:
        profile = create_profile_interactively(profile_file)

    return profile.__dict__


def check_value(value: str) -> Optional[str]:
    if not value.strip():
        raise click.UsageError("Cannot be empty")
    return value


def create_profile_interactively(profile_path: Path) -> Profile:
    first_name = click.prompt("Enter your first name", value_proc=check_value)
    last_name = click.prompt("Enter your last name", value_proc=check_value)
    country = click.prompt("Enter your country", default="")
    area = click.prompt("Enter your area", default="")

    user_profile = {
        "first_name": first_name,
        "last_name": last_name,
        "area": area,
        "country": country,
    }
    profile = Profile(**user_profile)
    profile.save(CONFIG_FOLDER / "profile.json")

    return profile


def create_client(name: str, email: str) -> Client:
    client = Client(name, email)
    return client


def save_client(client: Client, clients_folder: Path = CLIENTS_FOLDER) -> int:
    if not clients_folder.exists():
        clients_folder.mkdir(parents=True, exist_ok=True)

    client_file = clients_folder / client.name

    client_json = client.to_json()
    try:
        with open(client_file, "w") as fp:
            fp.write(client_json)
        return 0
    except Exception:
        return 1


def create_task(
    date_due: Union[date, str],
    date_received: Union[date, str],
    job_number: str,
    job_type: str,
    quantity: float,
    total_quantity: float,
    job_path: Path,
    note: str,
) -> Job:
    task = Job(
        date_due=date_due,
        date_received=date_received,
        job_number=job_number,
        job_type=job_type,
        quantity=quantity,
        total_quantity=total_quantity,
        job_path=job_path,
        note=note,
    )
    return task


def save_job_to_file(
    client: Client,
    jobs: list[Job],
    jobs_folder: Path = JOBS_FOLDER,
) -> int:

    if not jobs_folder.exists():
        jobs_folder.mkdir(parents=True, exist_ok=True)
    client_jobs_file = jobs_folder / client.name

    jobs_list = []
    for job in jobs:
        jobs_list.append(job.to_dict())

    if client_jobs_file.exists():
        with open(client_jobs_file, "r") as fd:
            client_jobs_info = json.load(fd)
            client_jobs_info["jobs_list"].extend(jobs_list)
    else:

        client_jobs_info = {}
        client_jobs_info["client"] = client.to_dict()
        client_jobs_info["jobs_list"] = jobs_list

    job_json = json.dumps(
        client_jobs_info,
        indent=2,
        ensure_ascii=False,
    )

    try:
        with open(client_jobs_file, "w") as fp:
            fp.write(job_json)
        return 0
    except Exception as error:
        return 1


def get_date_received(date_received: str) -> date:

    try:
        if isinstance(int(date_received), int):
            date_r = int(date_received)
            if date_r > 0:
                date_r *= -1
            date_rec = date.today() + timedelta(days=date_r)
        return date_rec

    except ValueError:
        date_rec = datetime.strptime(date_received, DATE_FMT).date()
        return date_rec


def get_date_due(date_due: str) -> date:
    try:
        if isinstance(int(date_due), int):
            date_d = date.today() + timedelta(days=int(date_due))
        return date_d

    except ValueError:
        date_d = datetime.strptime(date_due, DATE_FMT).date()
        return date_d


def get_clients(clients_folder: Path = CLIENTS_FOLDER) -> list[Client]:
    clients = []
    if not clients_folder.exists():
        return []
    else:
        clients_files = clients_folder.iterdir()
        for client_file in clients_files:
            with open(client_file, "r") as fd:
                client_json = json.load(fd)
                clients.append(Client.from_json(client_json))
    return clients


def get_jobs(client_name: Optional[str] = None) -> ClientLists:
    jobs = []

    if Path(JOBS_FOLDER).exists():
        if client_name:
            client_jobs_files = Path(JOBS_FOLDER).iterdir()
            for client_job_file in client_jobs_files:
                if client_name.lower() not in client_job_file.name.lower():
                    continue

                else:
                    with open(client_job_file, "r") as fp:
                        client_json = json.load(fp)
                    jobs.append(ClientList(**client_json))
                    break
        else:
            job_files = Path(JOBS_FOLDER).iterdir()
            for job_file in job_files:
                with open(job_file, "r") as fp:
                    client_json = json.load(fp)
                jobs.append(ClientList(**client_json))

    return ClientLists(jobs)


def get_jobs_per_client() -> ClientLists:
    jobs = []
    if Path(JOBS_FOLDER).exists():
        job_files = Path(JOBS_FOLDER).iterdir()
        for job_file in job_files:
            with open(job_file, "r") as fp:
                client_json = json.load(fp)
            jobs.append(ClientList(**client_json))
    return ClientLists(jobs)


def update_job(job_number: str, d: dict = {}) -> int:
    updated = 1
    for job_file in Path(JOBS_FOLDER).iterdir():

        with open(job_file, "r") as fd:
            c_json = json.load(fd)
            jobs_list = c_json["jobs_list"]

            for idx, job in enumerate(jobs_list):
                if job["job_number"] == job_number:
                    job.update(d)
                    updated_job = Job.from_json(job)
                    jobs_list[idx] = updated_job.to_dict()
                    c_json["jobs_list"] = jobs_list
                    updated = 0
                    break  # Allow user to select if multiple jobs exists; Only updates the first instance

        with open(job_file, "w") as fd:
            json.dump(c_json, fd, indent=2, ensure_ascii=False)
    return updated


def filter_jobs_by_date(
    key: str,
    date_from: Union[date, str],
    date_to: Union[date, str],
    jobs: list[Job],
) -> list[Job]:

    filtered_jobs = []

    if isinstance(date_from, str):
        date_from = string_to_date(date_from)
    if isinstance(date_to, str):
        date_to = string_to_date(date_to)

    for job in jobs:
        date_key = string_to_date(job.to_dict()[key])

        if date_key is None:
            continue

        if (
            isinstance(date_key, date)
            and isinstance(date_from, date)
            and isinstance(date_to, date)
        ):
            if (date_key >= date_from) and (date_key <= date_to):
                filtered_jobs.append(job)
    return filtered_jobs


def generate_invoice_docx(client: Client, jobs: list[Job], amount: float) -> None:
    doc = DocxTemplate(Path(__file__).parent / "invoice_template.docx")

    data = {
        "invoice_number": random.randint(1, 100),
        "created": date.today().strftime(DATE_FMT),
        "due": (date.today() + timedelta(days=2)).strftime(DATE_FMT),
    }
    # implement get_transcriber_info function
    personal_data = get_profile()

    context = {
        "client": client,
        "jobs": jobs,
        "amount": amount,
        "data": data,
        "personal_data": personal_data,
    }

    doc.render(context)

    invoice_file_name = "%s-%s_invoice.docx" % (
        date.today().strftime(DATE_FMT),
        client.name,
    )

    if not Path(INVOICES_FOLDER).exists():
        Path(INVOICES_FOLDER).mkdir(parents=True, exist_ok=True)

    doc.save(Path(INVOICES_FOLDER) / invoice_file_name)


def generate_invoice_pdf(client: Client, jobs: list[Job], amount: float) -> None:
    data = {
        "invoice_number": random.randint(1, 100),
        "created": date.today().strftime(DATE_FMT),
        "due": (date.today() + timedelta(days=2)).strftime(DATE_FMT),
    }
    # implement get_transcriber_info function
    personal_data = get_profile()

    context = {
        "client": client,
        "jobs": jobs,
        "amount": amount,
        "data": data,
        "personal_data": personal_data,
    }

    template_loader = jinja2.FileSystemLoader(searchpath="./")
    template_env = jinja2.Environment(loader=template_loader)
    template_file = "invoice_template.html"
    template = template_env.get_template(template_file)
    output_text = template.render(context)

    invoice_file_name = "%s-%s_invoice.pdf" % (
        date.today().strftime(DATE_FMT),
        client.name,
    )

    if not Path(INVOICES_FOLDER).exists():
        Path(INVOICES_FOLDER).mkdir(parents=True, exist_ok=True)

    pdfkit.from_string(output_text, Path(INVOICES_FOLDER) / invoice_file_name)
