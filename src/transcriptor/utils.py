import re
from datetime import date, datetime
from fractions import Fraction
from pathlib import Path
from typing import Match, Optional, Pattern, Union

from audioread import audio_open
from magic import from_file


def date_to_string(
    date_obj: Union[str, date], date_fmt: str = "%Y-%m-%d"
) -> Union[str, date]:
    if date_obj is None or date_obj == "":
        return ""
    if isinstance(date_obj, str):
        return date_obj
    elif isinstance(date_obj, date):
        return date_obj.strftime(date_fmt)


def string_to_date(date_str: str, date_fmt: str = "%Y-%m-%d") -> Union[str, date]:
    if date_str is None or date_str == "":
        return ""
    if isinstance(date_str, date):
        return date_str
    else:
        return datetime.strptime(date_str, date_fmt).date()


def parse_job_number(zip_file: Optional[Path]) -> str:
    assert zip_file is not None
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
    assert zip_file is not None
    zip_file = Path(zip_file)
    job_name = zip_file.stem  # remove .zip extension
    date_due_pattern: Pattern = re.compile(
        r"(?:(?<=DUE)|(?<=BACK))\s(\d{1,2}\.\d{1,2})", re.I
    )

    date_due_matches: Optional[Match] = date_due_pattern.search(job_name)
    if date_due_matches:
        date_due = format_date(date_due_matches.group(1))
    else:
        date_due = ""

    return date_due  # Due date in %m.%d format 10.11 (October, 11)


def format_date(d: str, date_fmt: str = "%Y-%m-%d") -> str:
    try:
        date_string = "%s.%s" % (d, datetime.today().year)
        date_obj = datetime.strptime(date_string, "%m.%d.%Y")
        return date_obj.strftime(date_fmt)
    except ValueError:
        return ""


def get_media_files(task_folder: Optional[Path]) -> list[Path]:
    assert task_folder is not None
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
    return round(float(min), 0)


def get_quantity(quantity: Union[str, int, float], total_quantity: float) -> float:
    quantity_words = {"whole": 1, "half": 0.5, "quarter": 0.25}

    try:
        if isinstance(float(quantity), float):
            q = round(float(quantity), 0)
    except ValueError:
        try:
            if isinstance(quantity, str):
                q = round(float(Fraction(quantity) * total_quantity), 0)
        except ValueError:
            if isinstance(quantity, str):
                q = round(float(total_quantity * quantity_words[quantity.lower()]), 0)

    return q
