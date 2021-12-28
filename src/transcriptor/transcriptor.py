import zipfile
from client import Client
import shutil
from job import Job
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Type, List
import json
from utils import *

WORK_FOLDER = 'workfolder'
CLIENTS_DIR = 'clients'

def create_client(name=None, email=None):
    client = Client(name, email)

    clients_dir = Path(CLIENTS_DIR)

    if not clients_dir.exists():
        clients_dir.mkdir(parents=True, exist_ok=True)

    client_file = clients_dir / name

    if client_file.exists():
        pass # Notify client already exists
    else:
        with open(clients_dir/name, 'w') as fd:
            fd.write(client.to_json())

def get_client(name: str):
    client_file = Path(CLIENTS_DIR) / name

    with open(client_file, 'r') as fd:
        client_js = json.load(fd)

    client = Client.from_json(client_js)
    return client

def create_job( zip_file: Type[Path], client: Type[Client], date_received: date = datetime.today().strftime("%Y-%m-%d"),):

    job_number, date_due, job_type = get_missing_job_details(example_file)

    job = Job(date_received=date_received, job_number=job_number, type=job_type, date_due=date_due)

    job_folder_name = "%s-%s_DUE_%s" % (
        str(job.date_received),
        str(job.job_number),
        str(job.date_due)
    )
    job_folder = Path(WORK_FOLDER) / job_folder_name
    if not job_folder.exists() and not job_folder.is_dir():
        job_folder.mkdir(parents=True, exist_ok=True)
        new_zip_file = shutil.copy2(zip_file, job_folder) # should move
        zipfile.ZipFile(new_zip_file).extractall(job_folder)
    else:
        pass #Notify user folder already exists

    media_files = get_media_files(job_folder)
    selected_media_files = select_media_files(media_files)
    job.media_files, job.quantity = get_job_quantity(selected_media_files)
    # job.quantity = quantity
    return job

