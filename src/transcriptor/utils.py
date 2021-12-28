from magic import from_file
from audioread import audio_open
from whaaaaat import prompt
from typing import Type, List
from pathlib import Path
from client import Client
import json
import re
from math import floor
from datetime import datetime, timedelta
from functools import reduce

def parse_job_details(zip_file: Type[Path]) -> tuple:
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

def get_missing_job_details(zip_file: Type[Path]) -> tuple:
    job_number, due_date, is_expedite = parse_job_details(zip_file)

    if job_number is None:
        job_number = input("Enter Job Number: ")

    if not is_expedite:
        # job_type = input("Enter Job Type: ")
        x = [{
            'type': 'rawlist',
            'name': 'job_type',
            'message': 'Select job type',
            'choices': ['Normal', 'Interpreted', 'Expedite']
        }]
        selected_type = prompt(x)
        job_type = selected_type['job_type']
    else:
        job_type = 'Expedite'

    return job_number, format_date(due_date), job_type

def format_date(d) -> str:
    if d is None:
        return ''
    try:
        if isinstance(abs(int(d)), int):
            d = datetime.today() + timedelta(abs(int(d)))

    except ValueError:
        date_string = '%s.%s' % (d, datetime.today().year)
        d = datetime.strptime(date_string, '%m.%d.%Y')

    return d.strftime("%Y-%m-%d")

def get_media_files(job_folder: List[Path]) -> list:
    media_files = []

    files = [f for f in job_folder.iterdir()]
    for file in files:
        file_type = from_file(str(file), mime=True)
        if 'audio' in file_type or 'video' in file_type:
            media_files.append(file)
    return sorted(media_files)

def get_duration(media_file: Path) -> float:
    return audio_open(media_file).duration

def get_numerical_value(s: str):
    d = {'whole': 1, 'half': 0.5, '1/2': 0.5, 'quarter': 0.25, '1/4': 0.25}
    return d[s]

def select_media_files(media_files: List[Path]) -> str:
    choices = [{
        'type': 'checkbox',
        'message': 'Select media',
        'name': 'selected_media_files',
        'choices': [{'name': str(x.absolute())} for x  in media_files],
    }]
    selected_media_files = prompt(choices)
    return selected_media_files['selected_media_files']

def to_minutes(seconds: float) -> int:
    minutes = floor(int(seconds / 60))
    return minutes

def get_job_quantity(media_files: List[str]) -> tuple:
    def g(filename):
        x = [{
            'type': 'input',
            'name': 'quantity',
            'message': f"Selected media file: {str(filename)}\n Enter quantity: ",
        }]
        return x

    t = []

    for media_file in media_files:
        media_file_data = {}
        media_file_data['media_file'] = media_file
        media_file_data['total_min'] = to_minutes(get_duration(Path(media_file)))
        quantity = prompt(g(media_file))
        quantity_value = quantity['quantity']
        try:
            if isinstance(float(quantity_value), float):
                media_file_data['quantity'] = to_minutes(float(quantity_value))
        except ValueError:
            b = get_numerical_value(quantity_value)
            media_file_data['quantity'] = to_minutes((b * get_duration(Path(media_file))))
        t.append(media_file_data)

    total = round(reduce((lambda a, b: a+b), [q['quantity'] for q in t]), 1)
    return t, total

def get_all_clients(clients_folder: str):
    clients = []
    for client_file in Path(clients_folder).iterdir():
        with open(client_file, 'r') as fd:
            client = Client.from_json(json.load(fd))
            clients.append(client)
    return clients

def select_client(clients: List[Type[Client]]):
    choices = [{
        'type': 'rawlist',
        'name': 'client',
        'message': 'Select client',
        'choices': [str(client.name) for client in clients]
    }]
    selected_client = prompt(choices)
    print(selected_client['client'])
    for c in clients:
        if (c.name == selected_client['client']):
            client = c
            return client

def get_new_client_details():
    x = [
    {
        'type': 'input',
        'name': 'name',
        'message': 'Enter clients name:',
    },
    {
        'type': 'input',
        'name': 'email',
        'message': 'Enter clients email:',
    },
    ]

    details = prompt(x)
    client = Client.from_json(details)
    return client
