import json
from datetime import datetime, timedelta, date

from pathlib import Path
from transcriptor import CONF_FILE
from transcriptor.client import Client
from transcriptor.job import Job
from transcriptor.utils import parse_job_details, string_to_date, read_settings, create_default_settings
from transcriptor.ui import input_menu

def check_settings():
    if Path(CONF_FILE).exists():
        settings = read_settings()
    else:
        settings = create_default_settings()

    return settings

def create_client(name=None, email=None) -> Client:
    if name is None or email is None:
        return None

    client = Client(name, email)
    return client

def save_client_to_file(client):
    clients_folder = Path(check_settings().clients_folder)
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

def create_job(date_received, job_number, job_type, total_quantity, date_due):
    job = Job(
        date_received = date_received,
        job_number = job_number,
        job_type = job_type,
        total_quantity = total_quantity,
        date_due=date_due,
    )
    return job

# def save_job_to_file(job):
#     job_json = job.to_json()
#     try:
#         with open('jobs.txt', 'w') as fp:
#             fp.write(job_json)
#         return True
#     except Exception as error:
#         print(error)
#         return False

def save_client_job_to_file(client, job):
    job_folder = Path(check_settings().job_folder)
    if not job_folder.exists():
        job_folder.mkdir(parents=True, exist_ok=True)
    client_jobs_file = job_folder / client.name

    client_job_dict = {}
    client_job_dict['client'] = client.to_dict()

    job_list = []
    job_list.append(job.to_dict())
    client_job_dict['job_list'] = job_list

    job_json = json.dumps(
        client_job_dict,
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
    job_number, date_due = parse_job_details(zip_file)

    return job_number, date_due

def get_date_received(date_received=None):
    if (date_received is None) or (not date_received):
        date_received = input_menu(
            name='date_received',
            msg='Enter date received [Year-Month-Date]: ',
            default=date.today().strftime('%Y-%m-%d'),
        )['date_received']
        date_rec = datetime.strptime(date_received, '%Y-%m-%d')

    elif not isinstance(date_received, int):
        date_rec = datetime.strptime(date_received, '%Y-%m-%d')

    elif isinstance(date_received, int):
        date_rec = date.today() + timedelta(days=date_received)

    return date_rec

if __name__ == "__main__":

    zip = "/home/kamikaze/Documents/Wera/Transcription/Wach/Chynna Barbosa/2021-11-12-514779_DUE_11.15_(VICTOR)/514779 DUE 11.15 (VICTOR).zip"

    # zip = "/home/kamikaze/Documents/Wera/Transcription/Wach/Chynna Barbosa/2021-11-12-514779/(VICTOR)/514779(VICTOR).zip"
    client = create_client('john')
    if client is None:
            client_name = input_menu(name='client_name', msg='Enter client name: ')['client_name']
            client_email = input_menu(name='client_email', msg='Enter client email: ')['client_email']
            client =  Client(client_name, client_email)
    date_received = get_date_received()
    job_number, date_due = get_job_details_from_zip(zip)
    if job_number is None:
        job_number = input_menu(name='job_number', msg='Enter job number: ')['job_number']
    if date_due is None:
        date_due = input_menu(name='date_due', msg='Enter date due: ')['date_due']
    if date_due == '':
        date_due = None
    job = create_job(date_received=date_received, job_number=job_number, job_type='Normal',  total_quantity=60, date_due=date_due)
    save_client_job_to_file(client, job)

