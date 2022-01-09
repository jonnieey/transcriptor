import json
import sys

from datetime import datetime, timedelta, date

from transcriptor.client import Client
from transcriptor.job import Job

from transcriptor.utils import (
    parse_job_number,
    parse_job_due_date,
    SETTINGS,
)

CONFIG_FOLDER, DATE_FMT = SETTINGS['config_folder'], SETTINGS['date_fmt']

def create_client(name=None, email=None):
    if name is None or email is None:
        return None

    client = Client(name, email)
    return client

def save_client_to_file(client, clients_folder):
    if not clients_folder.exists():
        clients_folder.mkdir(parents=True, exist_ok=True)

    client_file = clients_folder / client.name

    client_json = client.to_json()
    try:
        with open(client_file, 'w') as fp:
            fp.write(client_json)
        return True
    except Exception as error:
        print(error)
        return False

def create_task(
    date_due,
    date_received,
    job_number,
    job_type,
    quantity,
    total_quantity,
):
    task = Job(
        date_due=date_due,
        date_received = date_received,
        job_number = job_number,
        job_type = job_type,
        quantity=quantity,
        total_quantity = total_quantity,
    )
    return task

def save_client_job_to_file(client, jobs, job_folder):
    if not job_folder.exists():
        job_folder.mkdir(parents=True, exist_ok=True)
    client_jobs_file = job_folder / client.name

    jobs_list = []
    for job in jobs:
        jobs_list.append(job.to_dict())

    if client_jobs_file.exists():
        with open(client_jobs_file, 'r') as fd:
            client_jobs_info = json.load(fd)
            client_jobs_info['jobs_list'].extend(jobs_list)
    else:

        client_jobs_info = {}
        client_jobs_info['client'] = client.to_dict()
        client_jobs_info['jobs_list'] = jobs_list

    job_json = json.dumps(
        client_jobs_info,
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    )

    try:
        with open(client_jobs_file, 'w') as fp:
            fp.write(job_json)
        return True
    except Exception as error:
        print(error)
        return False

def get_job_details_from_zip(zip_file):
    job_number = parse_job_number(zip_file)
    date_due =  parse_job_due_date(zip_file)
    return job_number, date_due

def get_date_received(date_received=None):
    if date_received is None:
        return None

    elif date_received == '':
        return date.today()

    try:
        date_received = int(date_received)
        if date_received > 0:
            date_received *= -1
        date_rec = date.today() + timedelta(days=int(date_received))
        return date_rec

    except ValueError:
        try:
            date_rec = datetime.strptime(date_received, DATE_FMT).date()
            return date_rec
        except ValueError:
            print("Enter valid date [Year-month-day] format")
            sys.exit(1)

def get_date_due(date_due=None):
    try:
        date_due = abs(int(date_due))
        date_d = date.today() + timedelta(days=date_due)
        return date_d

    except ValueError:
        try:
            date_d = datetime.strptime(date_due, DATE_FMT).date()
            return date_d
        except ValueError:
            print("Enter valid date [Year-month-day] format")
            sys.exit(1)

def get_all_clients(clients_folder):
    clients = []
    if not clients_folder.exists():
        return []
    else:
        clients_files = clients_folder.iterdir()
        for client_file in clients_files:
            with open(client_file, 'r') as fd:
                client_json = json.load(fd)
                clients.append(Client().from_json(client_json))
    return clients
