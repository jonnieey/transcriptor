from pathlib import Path
import re
import mimetypes
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


def date_to_str(date_obj: datetime, date_fmt: str) -> str:
    """
    Convert a datetime object to a date string.

    Arguments:
        date_obj: A datetime object.
        date_fmt: Date format string.

    Retuns:
        A string representing the date in the given format,
    """
    return date_obj.strftime(date_fmt)


def get_media_files(directory: Path) -> list[Path]:
    """
    Get all media files in a directory.

    Arguments:
        directory: Directory to get media files from.
    """
    for file in directory.glob("**/*"):
        if file.is_file():
            mime_type, _ = mimetypes.guess_type(str(file))
            if (
                mime_type
                and mime_type is not None
                and (
                    mime_type.startswith("audio/")
                    or mime_type.startswith("video/")
                    or mime_type == "application/octet-stream"
                )
            ):
                yield file


def next_non_existent_file(filename):
    """
    Generate name for next non-existant file
    Example:
         if "test.txt" exists then next file will be
        "test_1.txt"

    Arguments:
        filename: Name of file

    Returns:
        Name of next non-existant file
    """
    base_dir = str(Path(filename).parent.absolute())
    nf = filename
    root, ext = Path(nf).stem, Path(nf).suffix
    i = 0
    while Path(nf).exists():
        i += 1
        nf = f"{base_dir}/{root}_{i}{ext}"
    return Path(nf)


def round_up(number):
    if number % 0.5 == 0:
        return number
    else:
        return number + 0.5 - (number % 0.5)
