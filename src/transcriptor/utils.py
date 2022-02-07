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
    """
    Convert date object to string.

    Arguments:
        date_obj: Instance of date object.
        date_fmt: Date format string.

    Returns:
        A date string
    """
    if date_obj is None or date_obj == "":
        return ""
    if isinstance(date_obj, str):
        return date_obj
    elif isinstance(date_obj, date):
        return date_obj.strftime(date_fmt)


def string_to_date(date_str: str, date_fmt: str = "%Y-%m-%d") -> Union[str, date]:
    """
    Convert string to date object.

    Arguments:
        date_str: Date string.
        date_fmt: Date format string.

    Returns:
        A date object.
    """
    if date_str is None or date_str == "":
        return ""
    if isinstance(date_str, date):
        return date_str
    else:
        return datetime.strptime(date_str, date_fmt).date()


def parse_job_number(zip_file: Optional[Path]) -> str:
    """
    Extract job number from file path name.

    Arguments:
        zip_file: Path to job zip file.

    Returns:
        Job number string.

    """
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
    """
    Extract due date from file path name.

    Arguments:
        zip_file: Path to job zip file.

    Returns:
        Job's due date string.

    """
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
    """
    Convert month.day ('%m.%d') string to full date string.

    Arguments:
        d: String with format of '%m.%d' date format.
        date_fmt: Date format string.

    Returns:
        A date string.

    """
    try:
        date_string = "%s.%s" % (d, datetime.today().year)
        date_obj = datetime.strptime(date_string, "%m.%d.%Y")
        return date_obj.strftime(date_fmt)
    except ValueError:
        return ""


def deformat_date(d: str, date_fmt: str = "%Y-%m-%d") -> str:
    """
    Convert full date string  to month.day ('%m.%d') string.

    Arguments:
        d: Date string
        date_fmt: Date format string.

    Returns:
        String with format of '%m.%d' date format.

    """
    try:
        if isinstance(d, datetime) or isinstance(d, date):
            date_object = d
        elif isinstance(d, str):
            date_object = datetime.strptime(d, date_fmt)
        return date_object.strftime("%m.%d")
    except ValueError:
        return ""


def get_media_files(task_folder: Optional[Path]) -> list[Path]:
    """
    Get all media files in a directory.

    Arguments:
        task_folder: Path to task/work folder.

    Returns:
        List of media file paths.
    """
    assert task_folder is not None
    media_files = []

    files = [f for f in task_folder.iterdir() if not f.is_dir()]
    for file in files:
        file_type = from_file(str(file), mime=True)
        if "audio" in file_type or "video" in file_type:
            media_files.append(file)
    return sorted(media_files)


def get_media_duration(media_file: Path) -> float:
    """
    Get media duration.

    Arguments:
        media_file: Path to media file.

    Returns:
        Duration/Length of media file in minutes.

    """
    return sec_to_min(audio_open(media_file).duration)


def sec_to_min(seconds: float) -> float:
    """
    Convert seconds to minutes.

    Arguments:
        seconds: Duration in seconds.

    Returns:
        Duration in minutes

    """
    min = (seconds // 60) + (seconds % 60) / 60
    return round(float(min), 0)


def get_quantity(quantity: Union[str, int, float], total_quantity: float) -> float:
    """
    Get quantity of work.

    Arguments:
        quantity: A float,
                  A Fraction string (1/2) or
                  A word (whole, half, quarter) *supported

    Returns:
        Quantity of job.

    """
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


def dict_values_string(d: dict) -> list[str]:
    """
    Convert dictionary values to string.

    Arguments:
        d: A dictionary.

    Returns:
        A list of dictionary value strings.
    """
    values_list = list(map(str, d.values()))
    return values_list


def filter_list(keyword: str, jobs_rows: list[list[str]]):
    """
    Filter list according to keyword.

    Arguments:
        keyword: Word to filter list.
        job_rows: A list of list of string.

    Returns:
        A list of keyword filtered lists.

    """
    filtered_lists = filter(lambda b: b if keyword in [f for f in b] else [], jobs_rows)
    return list(filtered_lists)
