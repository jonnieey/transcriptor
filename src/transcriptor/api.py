import shutil
import sys
import zipfile

import click
from tabulate import tabulate

from transcriptor.methods import (
    create_client,
    create_task,
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
        if client_name == client_obj.name:
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
        print(error)
        sys.exit(1)

    tasks = []

    media_files = get_media_files(job_folder)
    for media_file in media_files:
        task = {}

        print(media_file)
        work_on_file = ""
        # while work_on_file == "":
        work_on_file = click.prompt("? Work on this file [Y/n]: ")
        if work_on_file.lower() == "y":
            total_quantity = get_media_duration(media_file)
            job_type = click.prompt(
                "Specify job type", type=click.Choice(["Normal", "Interpreted", "Expedite"]), show_choices=True
            )
            quantity = get_quantity(click.prompt(" Enter quantity of task"), total_q=total_quantity)
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
    headers = ["Name", "Email"]
    clients_table = tabulate(
        sorted([[client.name, client.email] for client in clients]),
        headers=headers,
        tablefmt="fancy_grid",
        showindex=True,
    )
    print(clients_table)
    return clients


def list_client_jobs(client_name):
    raw_jobs = get_jobs(client_name)
    if raw_jobs is None:
        return
    jobs = []

    for job in raw_jobs:
        job.pop("job_path")
        jobs.append(job)

    totals_headers = {k: None for k in jobs[0]}  # To maintain cell width
    totals_headers[list(totals_headers.keys())[0]] = "TOTALS"
    totals_headers[list(totals_headers.keys())[-2]], totals_headers[list(totals_headers.keys())[-1]] = get_totals(jobs)

    jobs.append(totals_headers)

    print(tabulate(jobs, headers="keys", tablefmt="fancy_grid"))
    print()


def list_all_jobs():
    raw_jobs = get_jobs()
    if raw_jobs is None:
        return
    jobs = []

    for job in raw_jobs:
        job.pop("job_path")
        jobs.append(job)

    totals_headers = {k: None for k in jobs[0]}  # To maintain cell width
    totals_headers[list(totals_headers.keys())[0]] = "TOTALS"
    totals_headers[list(totals_headers.keys())[-2]], totals_headers[list(totals_headers.keys())[-1]] = get_totals(jobs)

    jobs.append(totals_headers)

    print(tabulate(jobs, headers="keys", tablefmt="fancy_grid"))
    print()
