from transcriptor.client import Client
from transcriptor.job import Job
from transcriptor.utils import parse_job_details
import json

def create_client(name, email) -> Client:
    client = Client(name, email)
    return client

def save_client_to_file(client):
    client_json = client.to_json()
    try:
        with open('clients.txt', 'w') as fp:
            fp.write(client_json)
        return True
    except Exception as error:
        print(error)
        return False

def create_job(date_received, job_number, job_type, total_quantity, date_due):
    job = Job(
        date_received = date_received,
        job_number = job_number,
        job_type = job_type,
        total_quantity = total_quantity,
        date_due=date_due,
    )
    return job

def save_job_to_file(job):
    job_json = job.to_json()
    try:
        with open('jobs.txt', 'w') as fp:
            fp.write(job_json)
        return True
    except Exception as error:
        print(error)
        return False

def save_client_job_to_file(client, job):
    client_job_dict = {}
    client_job_dict['client'] = client.to_dict()

    job_list = []
    job_list.append(job.to_dict())
    client_job_dict['job_list'] = job_list

    job_json = json.dumps(client_job_dict, indent=2, ensure_ascii=False, sort_keys=True)

    try:
        with open('jobs.txt', 'w') as fp:
            fp.write(job_json)
        return True
    except Exception as error:
        print(error)
        return False

def get_job_details_from_zip(zip_file):
    job_number, date_due = parse_job_details(zip_file)
    return job_number, date_due

if __name__ == "__main__":
    zip = "/home/kamikaze/Documents/Wera/Transcription/Wach/Chynna Barbosa/2021-11-12-514779_DUE_11.15_(VICTOR)/514779 DUE 11.15 (VICTOR).zip"
    client = create_client("Anderson", "Anderson@gmail.com")
    job_number, date_due = get_job_details_from_zip(zip)
    job = create_job(date_received='2021-12-12', job_number=job_number, job_type='Normal',  total_quantity=60, date_due=date_due)
    save_client_job_to_file(client, job)
