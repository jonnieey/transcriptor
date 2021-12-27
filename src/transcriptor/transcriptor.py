import zipfile
from client import Client
import shutil
from job import Job
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Type
import json
import re

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

def create_job(
    zip_file: Type[Path],
    client: Type[Client],
    date_received: date = datetime.today(),
):
    job_number, date_due, job_type = get_missing_job_details(example_file)

    job = Job(client=client, date_received=date_received, job_number=job_number, type=job_type, date_due=date_due)

    job_folder_name = "%s-%s_DUE_%s" % (
        str(job.date_received.strftime('%Y-%m-%d')),
        str(job.job_number),
        str(job.date_due.strftime('%Y-%m-%d'))
    )
    job_folder = Path(WORK_FOLDER) / job_folder_name
    if not job_folder.exists() and not job_folder.is_dir():
        job_folder.mkdir(parents=True, exist_ok=True)
    else:
        return

    new_zip_file = shutil.copy2(zip_file, job_folder) # should move
    zipfile.ZipFile(new_zip_file).extractall(job_folder)

def parse_job_details(zip_file: Type[Path]):
    job_name = zip_file.stem   #remove .zip extension
    # pattern = re.compile("(\d{6,8})(\sDUE\s\d{1,3}\.\d{1,3}).*$", re.IGNORECASE)
    # pattern = re.compile('(?=(\d{6,8})(?=.*?(DUE(?:\sBACK)?\s(?:\d{1,3}\.?){2})))')
    job_number_pattern = re.compile(r'(\d{6,8})')
    due_date_pattern = re.compile(r'(?:(?<=DUE)|(?<=BACK))\s(\d{2}\.\d{2})', re.I)
    is_expedite_pattern = re.compile('(?=Expedite)', re.I)

    try:
        job_number_matches = job_number_pattern.search(job_name)
        job_number = job_number_matches.group(1)
    except AttributeError:
        job_number = None

    try:
        due_date_matches = due_date_pattern.search(job_name)
        due_date = due_date_matches.group(1)
    except AttributeError:
        due_date = None

    try:
        is_expedite_matches = is_expedite_pattern.search(job_name)
        is_expedite = is_expedite_matches.group(1)
    except AttributeError:
        is_expedite = False

    return job_number, due_date, is_expedite # Due date in %m.%d format 10.11 (October, 11)

def get_missing_job_details(zip_file: Type[Path]):
    job_number, due_date, is_expedite = parse_job_details(zip_file)

    if job_number is None:
        job_number = input("Enter Job Number: ")

    # if due_date is None:
        # date_due = None
        # due_date = input("Enter Due Date Ex. (2032-12-24) or (5: in 5 days): ") # Accept integers eg +5 -> five days after current date

    if not is_expedite:
        job_type = input("Enter Job Type: ")
    else:
        job_type = 'Expedite'

    return job_number, format_date(due_date), job_type

def format_date(d):
    if d is None:
        return None
    try:
        if isinstance(abs(int(d)), int):
            d = datetime.today() + timedelta(abs(int(d)))

    except ValueError:
        date_string = '%s.%s' % (d, datetime.today().year)
        d = datetime.strptime(date_string, '%m.%d.%Y')

    return d

if __name__ == "__main__":
    c = get_client("Jon")
    example_file = Path("/home/kamikaze/Documents/Wera/Transcription/Wach/Chynna Barbosa/2021-11-07-513501_DUE_11.10_(VICTOR)/513501 DUE 11.10 (VICTOR).zip")
    # job_number, due_date, is_expedite =(parse_job_name(Path(example_file)))
    # create_job(c, job_number=job_number, due_date=due_date )
    # print(get_missing_job_details(Path(example_file)))
    # job_number, due_date, job_type = get_missing_job_details(Path(example_file))
    # print(due_date)
    create_job(zip_file=example_file, client=c)

    # j = create_job(c, job_number='34343', due_date='34343')
    # create_client("Jon", "Jon@gmail.com")
    # create_client("Anderson")
    # create_client("Anderson Njahi")
