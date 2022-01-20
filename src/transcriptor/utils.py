import json
import re
from datetime import date, datetime
from fractions import Fraction
from pathlib import Path
from typing import Match, Optional, Pattern, Union

from audioread import audio_open
from magic import from_file

from transcriptor.conf import get_config
from transcriptor.settings import Settings

config = get_config()


def create_default_settings() -> Settings:
    conf = Settings(
        clients_folder=config["clients_folder"],
        jobs_folder=config["jobs_folder"],
        works_folder=config["works_folder"],
        date_fmt=config["date_fmt"],
        config_folder=config["config_folder"],
        invoices_folder=config["invoices_folder"],
    )

    save_settings(conf)
    return conf


def save_settings(conf: Settings) -> None:

    if isinstance(conf.config_folder, Path):
        if not conf.config_folder.exists():
            conf.config_folder.mkdir(parents=True, exist_ok=True)

        config_file = conf.config_folder / "conf.json"

        with open(config_file, "w") as fp:
            fp.write(conf.to_json())


def read_settings() -> Settings:
    config_file = config["config_folder"] / "conf.json"
    if config_file.exists() and not config_file.is_dir():
        with open(config_file, "r") as fp:
            conf_json = json.load(fp)
    return Settings().from_json(conf_json)


def get_settings() -> dict:
    settings = read_settings()
    if settings is None:
        settings = create_default_settings()
    return settings.__dict__


DATE_FMT = get_settings()["date_fmt"]


def date_to_string(date_obj: Union[str, date]) -> Union[str, date]:
    if date_obj is None or date_obj == "":
        return ""
    if isinstance(date_obj, str):
        return date_obj
    elif isinstance(date_obj, date):
        return date_obj.strftime(DATE_FMT)


def string_to_date(date_str: str) -> Union[str, date]:
    if date_str is None or date_str == "":
        return ""
    if isinstance(date_str, date):
        return date_str
    else:
        return datetime.strptime(date_str, DATE_FMT).date()


def parse_job_number(zip_file: Path) -> str:
    if isinstance(zip_file, str):
        zip_file = Path(zip_file)
    job_name = zip_file.stem  # remove .zip extension
    job_number_pattern: Pattern = re.compile(r"(\d{6,8})")

    job_number_matches: Optional[Match] = job_number_pattern.search(job_name)

    if job_number_matches:
        job_number = job_number_matches.group(1)
    else:
        job_number = ""
    return job_number


def parse_job_due_date(zip_file: Path) -> str:
    if isinstance(zip_file, str):
        zip_file = Path(zip_file)
    job_name = zip_file.stem  # remove .zip extension
    date_due_pattern: Pattern = re.compile(r"(?:(?<=DUE)|(?<=BACK))\s(\d{2}\.\d{2})", re.I)

    date_due_matches: Optional[Match] = date_due_pattern.search(job_name)
    if date_due_matches:
        date_due = format_date(date_due_matches.group(1))
    else:
        date_due = ""

    return date_due  # Due date in %m.%d format 10.11 (October, 11)


def format_date(d: str) -> str:
    try:
        date_string = "%s.%s" % (d, datetime.today().year)
        date_obj = datetime.strptime(date_string, "%m.%d.%Y")
        return date_obj.strftime(DATE_FMT)
    except ValueError:
        return ""


def get_media_files(task_folder: Path) -> list[Path]:
    if isinstance(task_folder, str):
        task_folder = Path(task_folder)

    media_files = []

    files = [f for f in task_folder.iterdir()]
    for file in files:
        file_type = from_file(str(file), mime=True)
        if "audio" in file_type or "video" in file_type:
            media_files.append(file)
    return sorted(media_files)


def get_media_duration(media_file: Path) -> float:
    return sec_to_min(audio_open(media_file).duration)


def sec_to_min(seconds: float) -> float:
    min = (seconds // 60) + (seconds % 60) / 60
    return round(float(min), 1)


def get_quantity(quantity: Union[str, int, float], total_quantity: float) -> float:
    quantity_words = {"whole": 1, "half": 0.5, "quarter": 0.25}

    try:
        if isinstance(float(quantity), float):
            q = round(float(quantity), 1)
    except ValueError:
        try:
            if isinstance(quantity, str):
                q = round(float(Fraction(quantity) * total_quantity), 1)
        except ValueError:
            if isinstance(quantity, str):
                q = round(float(total_quantity * quantity_words[quantity.lower()]), 1)

    return q


# TODO implement function
def get_transcriber_info() -> dict:
    # placeholder for the function
    return {"name": "Anderson", "area": "Nairobi", "country": "Kenya"}


if __name__ == "__main__":
    print(get_settings())
