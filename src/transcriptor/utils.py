import re
from datetime import date
from datetime import datetime, timedelta
from pathlib import Path
from transcriptor.settings import Settings

DATE_FORMAT = '%Y-%m-%d'

def date_to_string(date_obj):
    if date_obj is None:
        return None
    elif isinstance(date_obj, date) or isinstance(date_obj, datetime):
        return date_obj.strftime(DATE_FORMAT)

def string_to_date(date_str):
    # Should accept other datetime formats
    return datetime.strptime(date_str, DATE_FORMAT).date()

def parse_job_details(zip_file):
    if isinstance(zip_file, str):
        zip_file = Path(zip_file)
    job_name = zip_file.stem   #remove .zip extension
    job_number_pattern = re.compile(r'(\d{6,8})')
    date_due_pattern = re.compile(r'(?:(?<=DUE)|(?<=BACK))\s(\d{2}\.\d{2})', re.I)

    try:
        job_number_matches = job_number_pattern.search(job_name)
        job_number = job_number_matches.group(1)
    except AttributeError:
        job_number = None

    try:
        date_due_matches = date_due_pattern.search(job_name)
        date_due = format_date(date_due_matches.group(1))
    except AttributeError:
        date_due = None

    return job_number, date_due    # Due date in %m.%d format 10.11 (October, 11)

def format_date(d):
    if d is None:
        return ''
    try:
        if isinstance(abs(int(d)), int):
            d = datetime.today() + timedelta(abs(int(d)))

    except ValueError:
        date_string = '%s.%s' % (d, datetime.today().year)
        d = datetime.strptime(date_string, '%m.%d.%Y')

    return d.strftime("%Y-%m-%d")

def create_default_settings():
    settings = Settings().generate_default_settings()
    settings.write_settings_to_file()

def read_settings():
    settings = Settings().read_settings_from_file()
    return settings


