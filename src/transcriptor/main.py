import json
import shutil
import zipfile
import sys

from datetime import datetime
from pathlib import Path

from transcriptor.job import Job
from transcriptor.client import Client

from transcriptor.utils import (
    get_missing_job_details, get_media_files, select_media_files,
    get_job_quantity, get_all_clients, select_client, get_new_client_details
)

WORK_FOLDER = 'workfolder'
CLIENTS_DIR = 'clients'
JOB_DIR = 'jobs'

def create_client(name='', email='') -> int:
    if (name == '') or (email == ''):
        client = get_new_client_details()
    else:
        client = Client(name=name, email=email)

    return client

def write_client(client: Client) -> bool:
    clients_dir = Path(CLIENTS_DIR)

    if not clients_dir.exists():
        clients_dir.mkdir(parents=True, exist_ok=True)

    client_file = clients_dir / str(client.name)

    if client_file.exists():
        print("Client already exists") # Notify client already exists
        return False

    else:
        with open(clients_dir/str(client.name), 'w') as fd:
            fd.write(client.to_json())
        return True

def create_job(zip_file: Path, date_received: str = datetime.today().strftime("%Y-%m-%d"),):

    job_number, date_due, job_type = get_missing_job_details(zip_file)

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
        print('Job folder alread exists')
        sys.exit(1)

    media_files = get_media_files(job_folder)
    selected_media_files = select_media_files(media_files)
    job.media_files, job.quantity = get_job_quantity(selected_media_files)
    # job.quantity = quantity
    return job

def write_job(zip_file: Path):
    clients = get_all_clients(CLIENTS_DIR)
    client = select_client(clients)
    job = create_job(zip_file)

    #Read from job file if exists
    #else create new

    d = {}
    d['client'] = client.to_dict()
    d['job_list'] = []
    d['job_list'].append(job.to_dict())

    jobs_dir = Path(JOB_DIR)

    if not jobs_dir.exists():
        jobs_dir.mkdir(parents=True, exist_ok=True)

    if (jobs_dir / str(client.name)).exists():
        with open(jobs_dir/str(client.name), 'r') as fd:
            jobs_info = json.load(fd)
            jobs_info['job_list'].append(job.to_dict())

        with open(jobs_dir/str(client.name), 'w') as fd:
            json.dump(jobs_info, fd, indent=2, ensure_ascii=False, sort_keys=True)

    else:
        with open(Path(JOB_DIR) / str(client.name), 'w') as fd:
            json.dump(d, fd, indent=2, ensure_ascii=False, sort_keys=True)

if __name__ == "__main__":
    create_client()
    # write_job(Path("/home/kamikaze/Documents/Wera/Transcription/Wach/Chynna Barbosa/2021-11-21-501363_DUE_11.23_-_12.6_(VICTOR)/501363 DUE 11.23 - 12.6 (VICTOR).zip"))
