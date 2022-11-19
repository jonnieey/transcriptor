import math
import os
import re
from pathlib import Path
from typing import Optional

from audioread import audio_open
from magic import from_file


def touch(file_paths: list[Path]):
    for file_path in file_paths:
        file_path = Path(file_path)
        file_path.parent.mkdir(exist_ok=True, parents=True)
        file_path.touch(exist_ok=True)


def mkdirp(dir_paths: list[Path]):
    for dir_path in dir_paths:
        dir_path = Path(dir_path)
        dir_path.mkdir(exist_ok=True, parents=True)


def sc(string: str):
    return string.replace(" ", "_")


def nc(string: str):
    return string.replace("_", " ")


def kebab_case(string: str):
    return string.replace(" ", "-")


def parse_job_number(file: str | Path):
    job_number_pattern: Pattern = re.compile(r"(\d{6,8})")
    job_number_matches: Optional[Match] = job_number_pattern.search(file)

    job_number = job_number_matches.group(1) if job_number_matches else ""
    return job_number


def parse_due_date(file: str | Path):
    date_due_pattern: Pattern = re.compile(
        r"(?:(?<=DUE)|(?<=BACK))[/\s-](\d{1,2}\.\d{1,2})", re.I
    )
    date_due_matches: Optional[Match] = date_due_pattern.search(file)
    date_due = date_due_matches.group(1) if date_due_matches else ""
    return date_due


def get_media_files(job_dir: Optional[Path]) -> list[Path]:
    media_files = []
    files = [f for f in job_dir.iterdir() if not f.is_dir()]

    for file in files:
        file_type = from_file(str(file), mime=True)
        types = ["audio", "video", "octet-stream"]
        if any(typ in file_type for typ in types):
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


def truncate(num, dp):
    return math.trunc(num * 10**dp) / (10 * dp)


def sec_to_min(seconds: float) -> float:
    """
    Convert seconds to minutes.

    Arguments:
        seconds: Duration in seconds.

    Returns:
        Duration in minutes

    """
    minutes = (seconds // 60) + (math.fmod(seconds, 60) / 60)
    return truncate(minutes, 2)


if __name__ == "__main__":
    print(parse_job_number("5234223-DUE-11-10"))
    print(parse_due_date("5234223-DUE 11.10"))
