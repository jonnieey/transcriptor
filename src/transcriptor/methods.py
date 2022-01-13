import json
import sys
from datetime import date, datetime, timedelta

from transcriptor.client import Client
from transcriptor.job import Job
from transcriptor.utils import get_config

settings = get_config()

CONFIG_FOLDER, DATE_FMT, JOBS_FOLDER, CLIENTS_FOLDER = (
    settings["config_folder"],
    settings["date_fmt"],
    settings["jobs_folder"],
    settings["clients_folder"],
)


def create_client(name=None, email=None):
    if name is None or email is None:
        return None

    client = Client(name, email)
    return client


def save_client(client, clients_folder=CLIENTS_FOLDER):
    if not clients_folder.exists():
        clients_folder.mkdir(parents=True, exist_ok=True)

    client_file = clients_folder / client.name

    client_json = client.to_json()
    try:
        with open(client_file, "w") as fp:
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
    job_path,
):
    task = Job(
        date_due=date_due,
        date_received=date_received,
        job_number=job_number,
        job_type=job_type,
        quantity=quantity,
        total_quantity=total_quantity,
        job_path=job_path,
    )
    return task


def save_job_to_file(client, jobs, jobs_folder=JOBS_FOLDER):
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
        # sort_keys=True,
    )

    try:
        with open(client_jobs_file, "w") as fp:
            fp.write(job_json)
        return True
    except Exception as error:
        print(error)
        return False


def get_date_received(date_received=None):
    if date_received is None:
        return None

    elif date_received == "":
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


def get_clients(clients_folder=CLIENTS_FOLDER):
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


def get_jobs(client_name=None):
    if JOBS_FOLDER.exists():
        if client_name is not None:
            client_jobs_file = JOBS_FOLDER / client_name
            if not client_jobs_file.exists():
                print("Client does not exist")
                return None
            else:
                with open(client_jobs_file, "r") as fp:
                    client_json = json.load(fp)
                    jobs = client_json["jobs_list"]
                    return jobs

        else:
            jobs = []
            job_files = JOBS_FOLDER.iterdir()
            for job_file in job_files:
                with open(job_file, "r") as fp:
                    client_json = json.load(fp)
                    [jobs.append(job) for job in client_json["jobs_list"]]
            return jobs


def update_job(job_number, d={}):
    for job_file in JOBS_FOLDER.iterdir():

        with open(job_file, "r") as fd:
            c_json = json.load(fd)
            jobs_list = c_json["jobs_list"]

            for idx, job in enumerate(jobs_list):
                if job["job_number"] == job_number:
                    job.update(d)
                    updated_job = Job.from_json(job)
                    jobs_list[idx] = updated_job.to_dict()
                    c_json["jobs_list"] = jobs_list
                    break  # Allow user to select if multiple jobs exists; Only updates the first instance

        with open(job_file, "w") as fd:
            json.dump(c_json, fd, indent=2, ensure_ascii=False)


def get_totals(jobs):
    amount_total = 0
    paid_amount_total = 0
    for job in jobs:
        if isinstance(job, dict):
            quantity = job['quantity']
            rate = job['job_rate']
            amount_paid = job['amount_paid']
        elif isinstance(job, Job):
            quantity = job.quantity
            rate = job.job_rate
            amount_paid = job.amount_paid

        amount_total += quantity * rate
        paid_amount_total +=  float(job.amount_paid)

    return amount_total, paid_amount_total
