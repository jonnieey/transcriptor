import math
import re
from datetime import date, datetime
from pathlib import Path
from typing import Match, Optional, Pattern

from audioread import audio_open
from magic import from_file


def touch(file_paths: list[Path | str]) -> None:
    """
    Create file and missing parent directories.

    Arguments:
        List of strings or Path objects of files to create
    """
    for file_path in file_paths:
        file_path = Path(file_path)
        file_path.parent.mkdir(exist_ok=True, parents=True)
        file_path.touch(exist_ok=True)


def mkdirp(dir_paths: list[Path | str]) -> None:
    """
    Create directories and missing parent directories. Like `mkdir -p` in linux.

    Arguments:
        List of strings or Path objects of directories to create.
    """
    for dir_path in dir_paths:
        dir_path = Path(dir_path)
        dir_path.mkdir(exist_ok=True, parents=True)


def convert_case(string: str, from_: str, to_: str) -> str:
    """
    Convert string case replacing from_ to to_.

    Arguments:
        string: String to convert case.
        from_: string to replace.
        to_: string to replace to.

    Returns:
        Case converted string
    """
    return string.replace(from_, to_)


sc = lambda s: convert_case(s, " ", "_")
nc = lambda s: convert_case(s, "_", " ")
kc = lambda s: convert_case(s, " ", "-")
tc = lambda s: nc(s).title()


def parse_job_number(file: str) -> str:
    """
    Get job number from path-like string.

    Arguments:
        file: Path-like string

    Returns:
        String (6-8 digit number string) ex. 534223.
    """
    job_number_pattern: Pattern = re.compile(r"(\d{6,8})")
    job_number_matches: Optional[Match] = job_number_pattern.search(file)

    job_number = job_number_matches.group(1) if job_number_matches else ""
    return job_number


def parse_due_date(file: str) -> str:
    """
    Get date due from path-like string.

    Arguments:
        file: Path-like string

    Returns:
        String (date string in format MM.DD) ex. 12.24
    """
    date_due_pattern: Pattern = re.compile(
        r"(?:(?<=DUE)|(?<=BACK))[/\s-](\d{1,2}\.\d{1,2})", re.I
    )
    date_due_matches: Optional[Match] = date_due_pattern.search(file)
    date_due = date_due_matches.group(1) if date_due_matches else ""
    return date_due


def get_media_files(directory: Path) -> list[Path]:
    """
    Get all media files in a directory.

    Arguments:
        directory: Directory to get media files from.

    Returns:
        List of media file Path objects.
    """
    media_files = []
    files = [f for f in directory.iterdir() if not f.is_dir()]

    for file in files:
        file_type = from_file(str(file), mime=True)
        types = ["audio", "video", "octet-stream"]
        if any(typ in file_type for typ in types):
            media_files.append(file)

    return sorted(media_files)


def get_media_duration(media_file: Path | str) -> float:
    """
    Get media duration.

    Arguments:
        media_file: Path to media file.

    Returns:
        Duration/Length of media file in minutes.

    """
    return sec_to_min(audio_open(media_file).duration)


def truncate(num: float, dp: int) -> float:
    """
    Truncate float to dp decimal places.

    Arguments:
        num: float number
        dp: decimal places to truncate to

    Returns:
        float
    """
    return math.trunc(num * 10**dp) / (10**dp)


def sec_to_min(seconds: float) -> float:
    """
    Convert seconds to minutes.

    Arguments:
        seconds: Duration in seconds.

    Returns:
        Duration in minutes

    """
    minutes = (seconds // 60) + ((seconds % 60) / 60)
    return truncate(minutes, 2)


def format_date(date_str: str, date_fmt: str):
    """
    Convert month.day ('%m.%d') string to full date string.

    Arguments:
        date_str: String with format of '%m.%d' date format.
        date_fmt: Date format string.

    Returns:
        A date string.

    """
    try:
        full_date_string = f"{date_str}.{date.today().year}"
        date_obj = datetime.strptime(full_date_string, "%m.%d.%Y")
        return date_obj.strftime(date_fmt)
    except ValueError:
        return ""


def str_to_date(date_string: str, date_fmt):
    return datetime.strptime(date_string, date_fmt)
