import json
import re

from datetime import datetime, timedelta
from functools import reduce
from math import floor
from pathlib import Path
from typing import Type, List

from audioread import audio_open
from magic import from_file
from whaaaaat import prompt, Validator, ValidationError

from transcriptor.client import Client

BASE_DIR = '/home/kamikaze/Documents/Wera/Transcription2'
WORK_FOLDER = BASE_DIR + '/workfolder'
CLIENTS_DIR = BASE_DIR +'/clients'
JOB_DIR = BASE_DIR + '/jobs'

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

def get_job_type(filename):
    x = [{
        'type': 'rawlist',
        'name': 'job_type',
        'message': 'Select job type',
        'message': f"Selected job type: {str(filename)}:",
        'choices': ['Normal', 'Interpreted', 'Expedite']
    }]
    rates = {'Normal': 0.40, 'Interpreted': 0.30, 'Expedite': 0.60}
    selected_type = prompt(x)
    job_type = selected_type['job_type']
    job_rate = rates[job_type]
    return {'job_type': job_type, 'job_rate': job_rate}

def get_missing_job_details(zip_file: Type[Path]) -> tuple:
    job_number, due_date, is_expedite = parse_job_details(zip_file)

    if job_number is None:
        job_number = input("Enter Job Number: ")

    if not is_expedite:
        # job_type = input("Enter Job Type: ")
        job_type = get_job_type(zip_file)['job_type']
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
        h = get_job_type(media_file)
        type, rate = h['job_type'], h['job_rate']
        media_file_data['type'] = type
        media_file_data['rate'] = rate
        quantity = prompt(g(media_file))
        quantity_value = quantity['quantity']
        try:
            if isinstance(float(quantity_value), float):
                media_file_data['amount'] = float(quantity_value) * rate
                media_file_data['quantity'] = round(float(quantity_value))
        except ValueError:
            b = get_numerical_value(quantity_value)
            quantity = to_minutes((b * get_duration(Path(media_file))))
            media_file_data['quantity'] = quantity
            media_file_data['amount'] = round(quantity * rate)
        t.append(media_file_data)

    total = round(reduce((lambda a, b: a+b), [q['amount'] for q in t]), 1)
    return t, total

def get_all_clients(clients_folder: str):
    clients = []
    try:
        clients_files = list(Path(clients_folder).iterdir())
    except FileNotFoundError:
        return []

    for client_file in clients_files:
        with open(client_file, 'r') as fd:
            client = Client.from_json(json.load(fd))
            clients.append(client)
    return clients

def create_client(name='', email='') -> int:
    if (name == '') or (email == ''):
        client = get_new_client_details()
    else:
        client = Client(name=name, email=email)

    write_client(client)

    return client

def write_client(client: Client) -> bool:
    clients_dir = Path(CLIENTS_DIR)

    # if not clients_dir.exists():
    #     clients_dir.mkdir(parents=True, exist_ok=True)

    create_dir(clients_dir)

    client_file = clients_dir / str(client.name)
    print(client_file)

    if client_file.exists():
        print("Client already exists") # Notify client already exists

    else:
        with open(clients_dir/str(client.name), 'w') as fd:
            fd.write(client.to_json())

def add_add(x):
    x.append('add client')
    return x

def select_client(clients):
    # if clients == []:
        # return []
    choices = [
        {
            'type': 'rawlist',
            'name': 'client',
            'message': 'Select client',
            'choices': add_add([str(client.name) for client in clients]),
        },
        {
            'type': 'input',
            'name': 'name',
            'message': 'Enter clients name:',
            'when': lambda selected_client: selected_client['client'] == 'add client'
        },
        {
            'type': 'input',
            'name': 'email',
            'message': 'Enter clients email:',
            'filter' : lambda v: v.lower(),
            'validate': EmailValidator,
            'when': lambda selected_client: selected_client['client'] == 'add client'
        },
    ]
    selected_client = prompt(choices)
    if selected_client['client'] == 'add client':
        selected_client.pop('client')
        client = Client.from_json(selected_client)
        write_client(client)
        return client

    else:
        for c in clients:
            if (c.name == selected_client['client']):
                client = c
                return client

class EmailValidator(Validator):
    def validate(self, doc):
        ok = re.match("^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", doc.text)
        if not ok:
            raise ValidationError(
                message='Enter a valid email address',
                cursor_position=len(doc.text),
            )

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
        'filter' : lambda v: v.lower(),
        'validate': EmailValidator,
    },
    ]

    details = prompt(x)
    client = Client.from_json(details)
    return client

def create_dir(path):
    path = Path(path) if isinstance(path, str) else path

    if path.exists() and path.is_dir():
        # print("Path already exists")
        return
    else:
        return path.mkdir(parents=True, exist_ok=True)

def check_dir_exists(path):
    if isinstance(path, str):
        path = Path(path)

    if path.exists() and (path.is_dir() or path.is_file()):
        return path
    else:
        return create_dir(path)
if __name__ == "__main__":
    clients = get_all_clients(CLIENTS_DIR)
    print(select_client(clients))
