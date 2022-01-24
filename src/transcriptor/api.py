import shutil
import sys
import zipfile
from datetime import date
from pathlib import Path
from typing import Union

import click
from beautifultable import BeautifulTable

from transcriptor.client import Client
from transcriptor.conf import get_config
from transcriptor.methods import (
    create_client,
    create_task,
    filter_jobs_by_date,
    generate_invoice_docx,
    generate_invoice_pdf,
    get_clients,
    get_jobs,
    get_jobs_per_client,
    get_totals,
    save_client,
    save_job_to_file,
    settings,
)
from transcriptor.utils import (
    get_media_duration,
    get_media_files,
    get_quantity,
    parse_job_due_date,
    parse_job_number,
)

CLIENTS_FOLDER, WORKS_FOLDER, JOBS_FOLDER = (
    settings.clients_folder,
    settings.works_folder,
    settings.jobs_folder,
)


def add_client(
    name: str,
    email: str,
    clients_folder: Path = CLIENTS_FOLDER,
) -> None:
    new_client = create_client(name=name, email=email)
    clients = get_clients(CLIENTS_FOLDER)
    if clients:
        for client in clients:
            if client == new_client:
                sys.exit("Client already exists")
            else:
                continue
        save_client(client=new_client, clients_folder=clients_folder)
    else:
        save_client(client=new_client, clients_folder=clients_folder)


def get_client_object(client_name: str) -> Client:
    clients = get_clients(CLIENTS_FOLDER)

    for client_obj in clients:
        if client_name.lower() in client_obj.name.lower():
            client = client_obj
            return client
        else:
            continue

    sys.exit("Client does not exist")


def create_job(
    zip_file: Path,
    date_received: str,
    date_due: str,
    client: Client,
    note: str = "",
) -> None:
    job_number = parse_job_number(zip_file)
    if date_due is None:
        date_due = parse_job_due_date(zip_file)

    job_folder_stem = "%s-%s_DUE_%s" % (date_received, job_number, date_due)
    job_folder = WORKS_FOLDER / client.name / job_folder_stem

    if not job_folder.exists():
        job_folder.mkdir(parents=True, exist_ok=True)

    new_zip_file = shutil.copy2(zip_file, job_folder)  # should move
    try:
        zipfile.ZipFile(new_zip_file).extractall(job_folder)
    except Exception as error:
        sys.exit(error)

    tasks = []

    media_files = get_media_files(job_folder)
    for media_file in media_files:

        click.echo(media_file)
        work_on_file = click.prompt(
            "Work on this file",
            type=click.Choice(["Y", "N"], case_sensitive=False),
            show_choices=True,
        )
        if work_on_file.lower() == "y":
            total_quantity = get_media_duration(media_file)
            job_type = click.prompt(
                "Specify job type",
                type=click.Choice(
                    ["Normal", "Interpreted", "Expedite"], case_sensitive=False
                ),
                show_choices=True,
            )
            quantity = get_quantity(
                click.prompt("Enter quantity of task", default=total_quantity),
                total_quantity=total_quantity,
            )
            task = create_task(
                date_received=date_received,
                job_number=job_number,
                job_type=job_type,
                total_quantity=total_quantity,
                quantity=quantity,
                date_due=date_due,
                job_path=job_folder,
                note=note,
            )
            task.amount = round(task.job_rate * task.quantity, 2)
            tasks.append(task)
        else:
            continue

    save_job_to_file(client, tasks, JOBS_FOLDER)


def list_clients() -> list[Client]:
    clients = get_clients(CLIENTS_FOLDER)
    headers = ["", "Name", "Email"]

    table = BeautifulTable()
    table.set_style(BeautifulTable.STYLE_BOX)
    table.columns.header = headers
    for idx, client in enumerate(clients):
        table.rows.append([idx, client.name, client.email])
    click.echo(table)

    return clients


def list_client_jobs(client_name: str, show_path=False) -> None:
    raw_jobs = get_jobs(client_name)

    if not raw_jobs:
        sys.exit("No Jobs available")

    terminal_size = shutil.get_terminal_size()
    table = BeautifulTable(maxwidth=terminal_size.columns)
    table.set_style(BeautifulTable.STYLE_BOX)

    jobs = []

    amount, amount_paid = get_totals(raw_jobs)

    if show_path is False:
        totals_list = [
            "TOTALS",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            amount,
            amount_paid,
            None,
        ]
        for job in raw_jobs:
            job_dict = job.to_dict()
            job_dict.pop("job_path")
            jobs.append(job_dict)

        headers = [x.replace("_", " ").title() for x in jobs[0]]
        table.columns.header = headers

    else:
        totals_list = [
            "TOTALS",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            amount,
            amount_paid,
            None,
            None,
        ]
        jobs.extend([j.to_dict() for j in raw_jobs])
        headers = [x.replace("_", " ").title() for x in jobs[0]]
        table.columns.header = headers
        table.columns.padding = 0

    for j in jobs:
        table.rows.append(list(j.values()))
    table.rows.append(totals_list)
    click.echo(table)


def list_all_jobs(per_client: bool = False, show_path: bool = False) -> None:
    terminal_size = shutil.get_terminal_size()

    if per_client:
        client_raw_jobs = get_jobs_per_client()
        if not client_raw_jobs:
            sys.exit("No Jobs available")
    else:
        raw_jobs = get_jobs()

        if not raw_jobs:
            sys.exit("No Jobs available")

    table = BeautifulTable(maxwidth=terminal_size.columns)
    table.columns.padding = 0
    table.set_style(BeautifulTable.STYLE_BOX)

    jobs = []

    if per_client is False:
        amount, amount_paid = get_totals(raw_jobs)
        if show_path is False:
            totals_list = [
                "TOTALS",
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                amount,
                amount_paid,
                None,
            ]

            for job in raw_jobs:
                job_dict = job.to_dict()
                job_dict.pop("job_path")
                jobs.append(job_dict)

            headers = [x.replace("_", " ").title() for x in jobs[0]]
            table.columns.header = headers

        else:
            totals_list = [
                "TOTALS",
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                amount,
                amount_paid,
                None,
                None,
            ]
            jobs.extend([j.to_dict() for j in raw_jobs])
            headers = [x.replace("_", " ").title() for x in jobs[0]]
            table.columns.header = headers
            table.columns.padding = 0

        for j in jobs:
            table.rows.append(list(j.values()))
        table.rows.append(totals_list)
        click.echo(table)

    else:

        jobs = []
        for client_job_dict in client_raw_jobs:
            amount, amount_paid = get_totals(client_job_dict["jobs_list"])

            if show_path is False:
                totals_list = [
                    "TOTALS",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    amount,
                    amount_paid,
                ]
                for job in client_job_dict["jobs_list"]:
                    job_dict = job.to_dict()
                    job_dict.pop("job_path")
                    jobs.append(job_dict)
            else:
                totals_list = [
                    "TOTALS",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    amount,
                    amount_paid,
                    None,
                ]
                jobs.extend([j.to_dict() for j in client_job_dict["jobs_list"]])

            headers = [x.replace("_", " ").title() for x in jobs[0].keys()]
            table.columns.header = headers

            click.echo(client_job_dict["client"]["name"])

            for j in jobs:
                table.rows.append(list(j.values()))
            table.rows.append(totals_list)
            click.echo(table)
            table.clear()


def create_invoice(
    client_name: str,
    date_from: Union[str, date],
    date_to: Union[str, date],
    as_docx: bool = False,
) -> None:
    client = get_client_object(client_name)
    raw_jobs = get_jobs(client_name)
    jobs = filter_jobs_by_date(
        key="date_submitted",
        date_from=date_from,
        date_to=date_to,
        jobs=raw_jobs,
    )
    amount, _ = get_totals(jobs)
    if as_docx:
        generate_invoice_docx(client, jobs, amount)
    else:
        generate_invoice_pdf(client, jobs, amount)
