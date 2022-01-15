import shutil
import sys
import zipfile

import click
from beautifultable import BeautifulTable

from transcriptor.methods import (
    create_client,
    create_task,
    filter_jobs_by_date,
    generate_invoice_docx,
    generate_invoice_pdf,
    get_clients,
    get_jobs,
    get_totals,
    save_client,
    save_job_to_file,
)
from transcriptor.utils import (
    get_config,
    get_media_duration,
    get_media_files,
    get_quantity,
    parse_job_due_date,
    parse_job_number,
)

settings = get_config()
CLIENTS_FOLDER, WORKS_FOLDER, JOBS_FOLDER = (
    settings["clients_folder"],
    settings["works_folder"],
    settings["jobs_folder"],
)


def add_client(name=None, email=None, clients_folder=CLIENTS_FOLDER):
    client = create_client(name=name, email=email)
    save_client(client=client, clients_folder=clients_folder)


def get_client_object(client_name):
    clients = get_clients(CLIENTS_FOLDER)

    for client_obj in clients:
        if client_name.lower() in client_obj.name.lower():
            client = client_obj
            return client
        else:
            continue


def create_job(zip_file, date_received, date_due, client):
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
        click.echo(error)
        sys.exit(1)

    tasks = []

    media_files = get_media_files(job_folder)
    for media_file in media_files:
        task = {}

        click.echo(media_file)
        work_on_file = click.prompt(
            "Work on this file", type=click.Choice(["Y", "N"], case_sensitive=False), show_choices=True
        )
        if work_on_file.lower() == "y":
            total_quantity = get_media_duration(media_file)
            job_type = click.prompt(
                "Specify job type",
                type=click.Choice(["Normal", "Interpreted", "Expedite"], case_sensitive=False),
                show_choices=True,
            )
            quantity = get_quantity(click.prompt("Enter quantity of task"), total_q=total_quantity)
            task = create_task(
                date_received=date_received,
                job_number=job_number,
                job_type=job_type,
                total_quantity=total_quantity,
                quantity=quantity,
                date_due=date_due,
                job_path=job_folder,
            )
            task.amount = task.job_rate * task.quantity
            tasks.append(task)
        else:
            continue

    save_job_to_file(client, tasks, JOBS_FOLDER)


def list_clients():
    clients = get_clients(CLIENTS_FOLDER)
    headers = ["", "Name", "Email"]

    table = BeautifulTable()
    table.set_style(BeautifulTable.STYLE_BOX)
    table.columns.header = headers
    for idx, client in enumerate(clients):
        table.rows.append([idx, client.name, client.email])
    click.echo(table)

    return clients


def list_client_jobs(client_name, show_path=False):
    raw_jobs = get_jobs(client_name)
    if raw_jobs is None:
        return

    terminal_size = shutil.get_terminal_size()
    table = BeautifulTable(maxwidth=terminal_size.columns)

    amount, amount_paid = get_totals(raw_jobs)
    if show_path is False:
        totals_list = ["TOTALS", None, None, None, None, None, None, None, None, amount, amount_paid]
        for job in raw_jobs:
            job.pop("job_path")
        headers = [x.replace("_", " ").title() for x in list(raw_jobs[0].keys())]
        table.columns.header = headers
    else:
        totals_list = ["TOTALS", None, None, None, None, None, None, None, None, amount, amount_paid, None]
        headers = [x.replace("_", " ").title() for x in list(raw_jobs[0].keys())]
        table.columns.header = headers
        table.columns.padding = 0

    table.set_style(BeautifulTable.STYLE_BOX)

    for job in raw_jobs:
        table.rows.append(list(job.values()))
    table.rows.append(totals_list)
    click.echo(table)


def list_all_jobs(per_client=False, show_path=False):
    terminal_size = shutil.get_terminal_size()

    if per_client:
        raw_jobs = get_jobs(per_client=per_client)
    else:
        raw_jobs = get_jobs()

    if raw_jobs is None:
        return

    table = BeautifulTable(maxwidth=terminal_size.columns)
    table.columns.padding = 0
    table.set_style(BeautifulTable.STYLE_BOX)

    if per_client is False:
        amount, amount_paid = get_totals(raw_jobs)
        if show_path is False:
            totals_list = ["TOTALS", None, None, None, None, None, None, None, None, amount, amount_paid]
            for job in raw_jobs:
                job.pop("job_path")
        else:
            totals_list = ["TOTALS", None, None, None, None, None, None, None, None, amount, amount_paid, None]

        headers = [x.replace("_", " ").title() for x in list(raw_jobs[0].keys())]
        table.columns.header = headers

        for job in raw_jobs:
            table.rows.append(list(job.values()))
        table.rows.append(totals_list)
        click.echo(table)

    else:

        for _ in raw_jobs:
            amount, amount_paid = get_totals(_["jobs_list"])

            if show_path is False:
                totals_list = ["TOTALS", None, None, None, None, None, None, None, None, amount, amount_paid]
                for job in _["jobs_list"]:
                    job.pop("job_path")
            else:
                totals_list = ["TOTALS", None, None, None, None, None, None, None, None, amount, amount_paid, None]

            headers = [x.replace("_", " ").title() for x in list(_["jobs_list"][0].keys())]
            table.columns.header = headers

            click.echo(_["client"]["name"])
            for job in _["jobs_list"]:
                table.rows.append(list(job.values()))
            table.rows.append(totals_list)
            click.echo(table)
            table.clear()


def create_invoice(client_name, date_from=None, date_to=None, as_docx=False):
    client = get_client_object(client_name)
    raw_jobs = get_jobs(client_name)
    jobs = filter_jobs_by_date(key="date_submitted", date_from=date_from, date_to=date_to, jobs=raw_jobs)
    amount, _ = get_totals(jobs)
    if as_docx:
        generate_invoice_docx(client, jobs, amount)
    else:
        generate_invoice_pdf(client, jobs, amount)
