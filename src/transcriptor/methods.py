import json
import os
import random
import shutil
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional, Union

import pdfkit
from docxtpl import DocxTemplate
from jinja2 import Environment, PackageLoader, select_autoescape

from transcriptor.client import Client
from transcriptor.client_list import ClientList, ClientLists
from transcriptor.conf import get_config
from transcriptor.job import Job
from transcriptor.profile import Profile
from transcriptor.settings import Settings
from transcriptor.utils import string_to_date

CONFIG_FOLDER = get_config()["config_folder"]
default_config_file = CONFIG_FOLDER / "conf.json"


def default_settings() -> Settings:
    """
    Get default settings.

    Returns:
        Settings instance.
    """
    settings = Settings(**get_config())
    return settings


def get_settings(config_file: Optional[Path] = default_config_file) -> Settings:
    """
    Load user configurations or use default configurations.

    Arguments:
        config_file: Path to user configurations file.

    Returns:
        Settings instance.
    """
    assert config_file is not None
    try:
        settings = Settings().load(config_file)
    except Exception:
        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            settings = default_settings()
            settings.save(config_file)
        except Exception:
            sys.exit("cannot create %s" % (config_file))
    return settings


settings = get_settings(CONFIG_FOLDER / "conf.json")


(
    CONFIG_FOLDER,
    JOBS_FOLDER,
    CLIENTS_FOLDER,
    DATE_FMT,
    INVOICES_FOLDER,
    RESOURCES_FOLDER,
) = (
    settings.config_folder,
    settings.jobs_folder,
    settings.clients_folder,
    settings.date_fmt,
    settings.invoices_folder,
    settings.resources_folder,
)


def create_client(name: str, email: str) -> Client:
    """
    Create Client instance.

    Arguments:
        name: Name of the client.
        email: Email of the client.

    Returns:
        Client instance.
    """
    client = Client(name, email)
    return client


def save_client(
    client: Client, clients_folder: Optional[Path] = CLIENTS_FOLDER
) -> None:
    """
    Save client information to file.

    Arguments:
        client: Client instance.
        clients_folder: Folder containing clients information files.

    """
    assert clients_folder is not None
    if not clients_folder.exists():
        clients_folder.mkdir(parents=True, exist_ok=True)

    client_file = clients_folder / client.name

    client_json = client.to_json()
    try:
        with open(client_file, "w") as fp:
            fp.write(client_json)
    except Exception:
        sys.exit("Cannot open file")


def create_task(
    date_due: Union[date, str],
    date_received: Union[date, str],
    job_number: str,
    job_type: str,
    quantity: float,
    total_quantity: float,
    job_path: Optional[Path],
    note: str,
) -> Job:
    """
    Create job/task instance.

    Arguments:
        date_due:  Job's date due string or date object.
        date_received: Job's date received string or date object.
        job_number: Job number string.
        job_type: Job number string string.
        quantity: Job quantity.
        total_quantity: Total job quantity.
        job_path: Path to job/task file.
        note: Job note.

    Returns:
        Job Instance.
    """
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
    jobs_folder: Optional[Path] = JOBS_FOLDER,
):

    """
    Save job to jobs file.

    Arguments:
        client: Client instance.
        jobs: list of Job instance.
        jobs_folder: Path to jobs file.

    """
    assert jobs_folder is not None
    if not jobs_folder.exists():
        jobs_folder.mkdir(parents=True, exist_ok=True)
    client_jobs_file = jobs_folder / client.name

    jobs_list = []
    for job in jobs:
        jobs_list.append(job.to_dict())

    if client_jobs_file.exists():
        with open(client_jobs_file, "r") as fd:
            fd.seek(0, os.SEEK_END)
            if fd.tell():
                fd.seek(0)

                client_jobs_info = json.load(fd)
                client_jobs_info["jobs_list"].extend(jobs_list)
            else:
                client_jobs_info = {}
                client_jobs_info["client"] = client.to_dict()
                client_jobs_info["jobs_list"] = jobs_list
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
    except Exception as error:
        sys.exit("Cannot write to file")


def get_date_received(date_received: str) -> date:
    """
    Get date received.

    Arguments:
        date_received: A date string, or an int string ('2').
            Positive dates are negated (Cannot receive job in future, yet. :D)

    Returns:
        A date object.
    """

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
    """
    Get date due.

    Arguments:
        date_due: A date string, or an int string ('2')
            Negative dates are converted to positive numbers

    Returns:
        A date object.
    """
    try:
        if isinstance(int(date_due), int):
            date_d = date.today() + timedelta(days=int(date_due))
        return date_d

    except ValueError:
        date_d = datetime.strptime(date_due, DATE_FMT).date()
        return date_d


def get_clients(clients_folder: Optional[Path] = CLIENTS_FOLDER) -> list[Client]:
    """
    Get clients from clients folder.

    Arguments:
        clients_folder: Path to clients folder.

    Return:
        List of Client instances.
    """
    clients = []
    assert clients_folder is not None
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
    """
    Get all jobs or client jobs.

    Arguments:
        client_name: Optional client name string.

    Returns:
        ClientLists instance.
    """
    jobs = []
    jobs_folder = JOBS_FOLDER

    assert jobs_folder is not None
    if jobs_folder.exists():
        if client_name:
            client_jobs_files = [
                j for j in jobs_folder.iterdir() if not j.suffix == ".bak"
            ]
            for client_job_file in client_jobs_files:
                if client_name.lower() not in client_job_file.name.lower():
                    continue

                else:
                    with open(client_job_file, "r") as fp:
                        client_json = json.load(fp)
                    jobs.append(ClientList(**client_json))
                    break
        else:
            job_files = [j for j in jobs_folder.iterdir() if not j.suffix == ".bak"]
            for job_file in job_files:
                with open(job_file, "r") as fp:
                    client_json = json.load(fp)
                jobs.append(ClientList(**client_json))

    return ClientLists(jobs)


def update_job(job_number: str, d: dict = {}) -> None:
    """
    Update job.

    Arguments:
        job_number: Job number string.
        d: Update dictionary

    """
    jobs_folder = JOBS_FOLDER
    assert jobs_folder is not None
    for job_file in [j for j in jobs_folder.iterdir() if not j.suffix == ".bak"]:

        with open(job_file, "r") as fd:
            c_json = json.load(fd)
            jobs_list = c_json["jobs_list"]

            for idx, job in enumerate(jobs_list):
                if job["job_number"] == job_number:
                    shutil.copy2(job_file, "%s.bak" % (job_file))
                    job.update(d)
                    updated_job = Job.from_json(job)
                    jobs_list[idx] = updated_job.to_dict()
                    c_json["jobs_list"] = jobs_list
                    updated = 0
                    # break  # Allow user to select if multiple jobs exists; Only updates the first instance

        with open(job_file, "w") as fd:
            json.dump(c_json, fd, indent=2, ensure_ascii=False)


def filter_jobs_by_date(
    key: str,
    date_from: Union[date, str],
    date_to: Union[date, str],
    jobs: list[Job],
) -> list[Job]:

    """
    Filter jobs by date.

    Arguments:
        key: Job date property (date_received, date_due, date_submitted).
        date_from: A date string.
        date_to: A date string.
        jobs: List of Job instances.

    Returns:
        List of filtered Job instances.
    """
    filtered_jobs = []

    if isinstance(date_from, str):
        date_from = string_to_date(date_from)
    if isinstance(date_to, str):
        date_to = string_to_date(date_to)

    for job in jobs:
        date_key = string_to_date(job.to_dict()[key])

        if date_key is None or date_key == "":
            continue

        assert isinstance(date_key, date)
        assert isinstance(date_from, date)
        assert isinstance(date_to, date)

        if (date_key >= date_from) and (date_key <= date_to):
            filtered_jobs.append(job)
    return filtered_jobs


def generate_invoice_docx(
    client: Client, jobs: list[Job], amount: float, user_profile: Profile
) -> None:
    """
    Generate docx invoice.

    Arguments:
        client: Client object.
        jobs:  list of Job instances.
        amount:  Amount value of job.
        user_profile: Profile Instance.

    """
    doc = DocxTemplate(Path(__file__).parent / "templates" / "invoice_template.docx")

    data = {
        "invoice_number": random.randint(1, 100),
        "created": date.today().strftime(DATE_FMT),
        "due": (date.today() + timedelta(days=2)).strftime(DATE_FMT),
    }
    # implement get_transcriber_info function
    personal_data = user_profile.__dict__

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

    invoices_folder = INVOICES_FOLDER
    assert invoices_folder is not None
    if not invoices_folder.exists():
        invoices_folder.mkdir(parents=True, exist_ok=True)

    doc.save(invoices_folder / invoice_file_name)


def generate_invoice_pdf(
    client: Client, jobs: list[Job], amount: float, user_profile: Profile
) -> None:
    """
    Generate pdf invoice.

    Arguments:
        client: Client object.
        jobs:  list of Job instances.
        amount:  Amount value of job.
        user_profile: Profile Instance.

    """
    env = Environment(
        loader=PackageLoader("transcriptor", "templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    data = {
        "invoice_number": random.randint(1, 100),
        "created": date.today().strftime(DATE_FMT),
        "due": (date.today() + timedelta(days=2)).strftime(DATE_FMT),
    }
    personal_data = user_profile.__dict__

    context = {
        "client": client,
        "jobs": jobs,
        "amount": amount,
        "data": data,
        "personal_data": personal_data,
    }

    template_file = "invoice_template.html"

    template = env.get_template(template_file)
    output_text = template.render(context)

    invoice_file_name = "%s-%s_invoice.pdf" % (
        date.today().strftime(DATE_FMT),
        client.name,
    )

    invoices_folder = INVOICES_FOLDER
    assert invoices_folder is not None
    if not invoices_folder.exists():
        invoices_folder.mkdir(parents=True, exist_ok=True)

    pdfkit.from_string(output_text, invoices_folder / invoice_file_name)


def get_template_type(initials: str = ""):
    """
    Get template type from template initials.

    Arguments:
        initials: Template initials.

    Returns:
        String of template type.
    """
    template_type_dict = {
        "nd": "Deposition Block File.doc",
        "nh": "Hearing Block File.doc",
        "ne": "Examination Under Oath Block File.doc",
        "zd": "Zoom Deposition Block File.doc",
        "zh": "Zoom Hearing Block File.doc",
        "ze": "Zoom Examination Under Oath Block File.doc",
        "tt": "Tape Transcript.doc",
        "di": "Deposition with Interpreter.docx",
        "me": "Compulsory Medical Exam Template.doc",
    }

    return template_type_dict[initials]


def get_template_file(client: str, template_type: str = ""):
    """
    Get template file from template type.

    Arguments:
        client: Client's name.
        template_type:  Template type string.

    Returns:
        Template file path object.
    """
    templates_folder = RESOURCES_FOLDER
    assert templates_folder is not None

    template_file = Path(templates_folder) / client / get_template_type(template_type)
    return template_file


def get_total_amount(jobs_list: list[Job]) -> float:
    """
    Get total amount.

    Arguments:
        jobs_list:  list of Job instances.

    Returns:
        Total amount of jobs.
    """
    return round(sum([job.amount for job in jobs_list]), 0)


def get_total_amount_paid(jobs_list: list[Job]) -> float:
    """
    Get total amount paid.

    Arguments:
        jobs_list:  list of Job instances.

    Returns:
        Total amount paid of jobs.
    """
    return round(sum([job.amount_paid for job in jobs_list]), 0)
