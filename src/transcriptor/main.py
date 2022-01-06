import json
import shutil
import zipfile
import sys
import argparse

from datetime import datetime
from pathlib import Path

from transcriptor.job import Job
from transcriptor.client import Client

from transcriptor.utils import (
    create_dir, get_all_clients, get_job_quantity, get_media_files,
    get_missing_job_details, get_new_client_details, select_client,
    select_media_files, create_client, write_client,
)
from transcriptor.settings import Settings

BASE_DIR = '/home/kamikaze/Documents/Wera/Transcription2'
WORK_FOLDER = BASE_DIR + '/workfolder'
CLIENTS_DIR = BASE_DIR +'/clients'
JOB_DIR = BASE_DIR + '/jobs'

def create_job(zip_file: Path, date_received: str = datetime.today().strftime("%Y-%m-%d"),):

    job_number, date_due, job_type = get_missing_job_details(zip_file)

    clients = get_all_clients(CLIENTS_DIR)
    if clients == []:
        client = create_client()
    else:
        client = select_client(clients)

    job = Job(date_received=date_received, job_number=job_number, type=job_type, date_due=date_due)

    work_folder_name = "%s-%s_DUE_%s" % (
        str(job.date_received),
        str(job.job_number),
        str(job.date_due)
    )

    workfolder = Path(WORK_FOLDER) /  client.name / work_folder_name

    if (create_dir(workfolder) is not None) or (list(workfolder.iterdir()) == []):
        new_zip_file = shutil.copy2(zip_file, workfolder) # should move
        zipfile.ZipFile(new_zip_file).extractall(workfolder)
    else:
        print('Job folder alread exists')

    media_files = get_media_files(workfolder)
    selected_media_files = select_media_files(media_files)
    job.media_files, job.quantity = get_job_quantity(selected_media_files)
    # job.quantity = quantity
    return job, client

def write_job(zip_file: Path):
    jobs_dir = Path(JOB_DIR)

    job, client = create_job(zip_file)

    #Read from job file if exists
    #else create new

    d = {}
    d['client'] = client.to_dict()
    d['job_list'] = []
    d['job_list'].append(job.to_dict())

    create_dir(jobs_dir) # return None if dir exists else creates it

    if (jobs_dir / str(client.name)).exists():
        with open(jobs_dir/str(client.name), 'r') as fd:
            jobs_info = json.load(fd)
            jobs_info['job_list'].append(job.to_dict())

        with open(jobs_dir/str(client.name), 'w') as fd:
            json.dump(jobs_info, fd, indent=2, ensure_ascii=False, sort_keys=True)

    else:
        with open(Path(JOB_DIR) / str(client.name), 'w') as fd:
            json.dump(d, fd, indent=2, ensure_ascii=False, sort_keys=True)

# def update_job_status(job: Job):

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', help='Create new task')
    parser.add_argument('-N', nargs='?', const=' ', help='')
    parser.add_argument('-c', nargs='?', const=' ', help='Specify client')

    write_job(Path("/home/kamikaze/Documents/Wera/Transcription/Wach/Chynna Barbosa/2021-11-21-501363_DUE_11.23_-_12.6_(VICTOR)/501363 DUE 11.23 - 12.6 (VICTOR).zip"))
