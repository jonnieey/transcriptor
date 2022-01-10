import json
import re
import zipfile
from datetime import date, datetime, timedelta
from fractions import Fraction
from math import floor
from pathlib import Path

from audioread import audio_open
from magic import from_file

from transcriptor.conf import get_config
from transcriptor.settings import Settings

config = get_config()


def create_default_config():
    conf = Settings(
        clients_folder=config["clients_folder"],
        jobs_folder=config["jobs_folder"],
        works_folder=config["works_folder"],
        date_fmt=config["date_fmt"],
        config_folder=config["config_folder"],
    )

    save_config_to_file(conf)
    return conf


def save_config_to_file(conf):
    config_file = conf.config_folder / "conf.json"
    if not conf.config_folder.exists():
        conf.config_folder.mkdir(parents=True, exist_ok=True)
    with open(config_file, "w") as fp:
        fp.write(conf.to_json())


def read_settings():
    config_file = config["config_folder"] / "conf.json"
    if config_file.exists() and not config_file.is_dir():
        with open(config_file, "r") as fp:
            conf_json = json.load(fp)
            return Settings().from_json(conf_json)


def get_settings():
    settings = read_settings()
    if settings is None:
        settings = create_default_config()
    return settings.__dict__


DATE_FMT = get_settings()["date_fmt"]


def date_to_string(date_obj):
    if date_obj is None:
        return None
    elif isinstance(date_obj, date) or isinstance(date_obj, datetime):
        return date_obj.strftime(DATE_FMT)


def string_to_date(date_str):
    return datetime.strptime(date_str, DATE_FMT).date()


def parse_job_number(zip_file):
    if isinstance(zip_file, str):
        zip_file = Path(zip_file)
    job_name = zip_file.stem  # remove .zip extension
    job_number_pattern = re.compile(r"(\d{6,8})")
    try:
        job_number_matches = job_number_pattern.search(job_name)
        job_number = job_number_matches.group(1)
    except AttributeError:
        job_number = None
    return job_number


def parse_job_due_date(zip_file):
    if isinstance(zip_file, str):
        zip_file = Path(zip_file)
    job_name = zip_file.stem  # remove .zip extension
    date_due_pattern = re.compile(r"(?:(?<=DUE)|(?<=BACK))\s(\d{2}\.\d{2})", re.I)

    try:
        date_due_matches = date_due_pattern.search(job_name)
        date_due = format_date(date_due_matches.group(1))
    except AttributeError:
        date_due = None

    return date_due  # Due date in %m.%d format 10.11 (October, 11)


def format_date(d):
    if d is None:
        return ""
    try:
        date_string = "%s.%s" % (d, datetime.today().year)
        d = datetime.strptime(date_string, "%m.%d.%Y")
        return d.strftime(DATE_FMT)
    except ValueError:
        pass


def extract_zip_to(zip_file, destination_folder):
    zipfile.ZipFile(zip_file).extractall(destination_folder)


def get_media_files(task_folder):
    if isinstance(task_folder, str):
        task_folder = Path(task_folder)

    media_files = []

    files = [f for f in task_folder.iterdir()]
    for file in files:
        file_type = from_file(str(file), mime=True)
        if "audio" in file_type or "video" in file_type:
            media_files.append(file)
    return sorted(media_files)


def get_media_duration(media_file):
    return sec_to_min(audio_open(media_file).duration)


def sec_to_min(seconds):
    return round(int(seconds / 60), 0)


def menu_from_list(l, msg=""):
    s = f"{msg}:\n"
    for idx, i in enumerate(l):
        s += " %s. %s\n" % (idx, i)
    return s


def get_quantity(q, total_q=0.0):
    quantity_words = {
        "whole": 1,
        "half": 0.5,
        "quarter": 0.25,
    }

    try:
        if isinstance(float(q), float):
            return float(q)
    except ValueError:
        try:
            quantity = round(float(Fraction(q) * total_q), 1)
            return quantity
        except ValueError:
            try:
                quantity = total_q * quantity_words[q]
                return quantity
            except Exception:
                return None
