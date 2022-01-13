import shutil
import sys

from tabulate import tabulate

from transcriptor.methods import (
    create_client,
    create_task,
    get_all_clients,
    get_all_jobs,
    get_client_jobs,
    get_totals,
    save_client_job_to_file,
    save_client_to_file,
)
from transcriptor.utils import (
    extract_zip_to,
    get_media_duration,
    get_media_files,
    get_quantity,
    get_settings,
    menu_from_list,
    parse_job_due_date,
    parse_job_number,
    remove_dict_key,
)

settings = get_settings()
CLIENTS_FOLDER, WORKS_FOLDER, JOBS_FOLDER = (
    settings["clients_folder"],
    settings["works_folder"],
    settings["jobs_folder"],
)


def add_client(name=None, email=None, clients_folder=CLIENTS_FOLDER):
    client = create_client(name=name, email=email)
    save_client_to_file(client=client, clients_folder=clients_folder)


def get_client_object(client_name):
    clients = get_all_clients(CLIENTS_FOLDER)
    if clients == []:
        name = input("Enter clients name: ")
        email = input("Enter clients email: ")
        client = create_client(name, email)
        save_client_to_file(client, CLIENTS_FOLDER)
        return client

    for client_obj in clients:
        if client_name == client_obj.name:
            client = client_obj
            return client
        else:
            continue
    clients_menu = menu_from_list([c.name for c in clients], msg="Select client")
    print(clients_menu)
    selected_client = int(input("client number: "))
    client = clients[selected_client]
    return client


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
        extract_zip_to(new_zip_file, job_folder)
    except Exception as error:
        print(error)
        sys.exit(1)

    tasks = []

    media_files = get_media_files(job_folder)
    for media_file in media_files:
        task = {}

        print(media_file)
        work_on_file = ""
        while work_on_file == "":
            work_on_file = input("? Work on this file [Y/n]: ").lower()

        if work_on_file == "y":
            total_quantity = get_media_duration(media_file)
            job_type = input("Specify job type [Normal, Interpreted, Expedite]:  ")
            quantity = get_quantity(input("?  Enter quantity of task:  "), total_q=total_quantity)
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

    save_client_job_to_file(client, tasks, JOBS_FOLDER)


def list_clients():
    clients = get_all_clients(CLIENTS_FOLDER)
    headers = ["Name", "Email"]
    clients_table = tabulate(
        [[client.name, client.email] for client in clients],
        headers=headers,
        tablefmt="fancy_grid",
        showindex=True,
    )
    print(clients_table)
    return clients


def list_client_jobs(client_name):
    raw_jobs = get_client_jobs(client_name)
    if raw_jobs is None:
        return None
    jobs = []
    for raw_job in raw_jobs:
        try:
            raw_job.pop("job_path")
            jobs.append(raw_job)
        except Exception:
            jobs.append(raw_job)
    t = {k: None for k, v in jobs[0].items()}
    t["date_received"] = "TOTALS"
    t["amount"], t["amount_paid"] = get_totals(jobs)
    jobs.append(t)
    jobs_table = tabulate(jobs, headers="keys", tablefmt="fancy_grid")
    return jobs_table


def list_all_jobs():
    all_jobs = get_all_jobs()

    new_all_jobs = []  # remove job_path key
    for jobs in all_jobs:  # get client's jobs
        x = {}
        for client_name, client_jobs in jobs.items():
            j = []
            for job in client_jobs:
                remove_dict_key(job, key="job_path")
                j.append(job)
            x[client_name] = j

        new_all_jobs.append(x)

    for i in new_all_jobs:
        for client_name, client_jobs in i.items():
            t = {k: None for k, v in client_jobs[0].items()}
            t["date_received"] = "TOTALS"
            t["amount"], t["amount_paid"] = get_totals(client_jobs)
            client_jobs.append(t)
            print(f"{client_name} JOBS\n")
            print(tabulate(client_jobs, headers="keys", tablefmt="fancy_grid"))
            print()
