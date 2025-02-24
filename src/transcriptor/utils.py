from pathlib import Path
import re
from datetime import datetime, date


def touch(file_paths: list[Path | str]) -> None:
    """
    Create files and any missing parent directories.

    Arguments:
        file_paths: List of strings or Path objects representing the files to create.
    """
    for file_path in map(Path, file_paths):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch(exist_ok=True)


def mkdirp(dir_paths: list[Path | str]) -> None:
    """
    Create directories and missing parent directories. Like `mkdir -p` in Linux.

    Args:
        dir_paths: A list of strings or Path objects representing directories to create.
    """

    for dir_path in map(Path, dir_paths):
        dir_path.mkdir(parents=True, exist_ok=True)


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
    pattern = re.compile(from_, re.IGNORECASE)
    return pattern.sub(to_, string)


def sc(s):
    return convert_case(s, r"[ -]", "_")


def nc(s):
    return convert_case(s, r"[-_]", " ")


def kc(s):
    return convert_case(s, r"[ _]", "-")


def tc(s):
    return nc(s).title()


TEMPLATE_MAPPING = {
    "zd": "Zoom Deposition Block Files.docx",
    "nh": "Hearing Block Files.docx",
    "zeo": "Zoom Examination Under Oath Block Files.docx",
    "zh": "Zoom Hearing Block Files.docx",
    "zus": "Zoom Unsworn Statement Block Files.docx",
    "zwc": "Zoom Workers Comp Deposition Block Files.docx",
    "tt": "Tape Transcript.docx",
    "me": "Compulsory Medical Exam Template.docx",
    "zdi": "Zoom Deposition Block File with Interpreter.docx",
    "od": "Overflow Deposition Block Files.docx",
    "oh": "Overflow Hearing Block Files.docx",
}


def str_to_date(date_string: str, date_fmt: str) -> datetime:
    """
    Convert a date string to a datetime object.

    Arguments:
        date_string (str): A string in the format '%m.%d'.
        date_fmt (str): The desired date format string.

    Returns:
        A datetime object representing the date in the given format,
    """
    if isinstance(date_string, (datetime, date)):
        return date_string
    return datetime.strptime(date_string, date_fmt)
