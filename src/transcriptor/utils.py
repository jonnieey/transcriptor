from magic import from_file
from audioread import audio_open
from whaaaaat import prompt, print_json, Separator
from typing import Type, List
from pathlib import Path
from client import Client
import json
import re
from datetime import datetime
from functools import reduce

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

    return d.strftime("%Y-%m-%d")

def get_media_files(job_folder: Type[Path]):
    media_files = []

    files = [f for f in job_folder.iterdir()]
    for file in files:
        file_type = from_file(str(file), mime=True)
        if 'audio' in file_type or 'video' in file_type:
            media_files.append(file)
    return sorted(media_files)

def get_duration(media_file: Type[Path]) -> float:
    return audio_open(media_file).duration

def get_numerical_value(s: str):
    d = {'whole': 1, 'half': 0.5, '1/2': 0.5, 'quarter': 0.25, '1/4': 0.25}
    return d[s]

def select_media_files(media_files: List[Type[Path]]):
    choices = [{
        'type': 'checkbox',
        'message': 'Select media',
        'name': 'selected_media_files',
        'choices': [{'name': str(x.absolute())} for x  in media_files],
    }]
    selected_media_files = prompt(choices)
    return selected_media_files['selected_media_files']

def get_job_quantity(media_files: List[str]) -> tuple:
    def g(filename):
        x = [{
            'type': 'input',
            'name': 'quantity',
            'message': f"{str(filename)}\nEnter quantity: ",
        }]
        return x

    t = []

    for media_file in media_files:
        media_file_data = {}
        media_file_data['media_file'] = media_file
        quantity = prompt(g(media_file))
        quantity_value = quantity['quantity']
        try:
            if isinstance(float(quantity_value), float):
                media_file_data['quantity'] = round(float(quantity_value), 1)
        except ValueError:
            b = get_numerical_value(quantity_value)
            media_file_data['quantity'] = round((b * get_duration(Path(media_file))) / 60, 1)
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


