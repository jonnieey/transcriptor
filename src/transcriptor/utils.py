import csv
import math
import mimetypes
import re
from datetime import datetime, timedelta
from decimal import Decimal
from fractions import Fraction
from io import StringIO
from pathlib import Path
from typing import List, Match, Optional, Pattern

import docx
from audioread import audio_open
from prompt_toolkit.validation import Validator


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


sc = lambda s: convert_case(s, r"[ -]", "_")
nc = lambda s: convert_case(s, r"[-_]", " ")
kc = lambda s: convert_case(s, r"[ _]", "-")
tc = lambda s: nc(s).title()


def parse_job_number(file: str) -> str:
    """
    Get job number from path-like string.

    Arguments:
        file: Path-like string

    Returns:
        String (6-8 digit number string) ex. 534223.
    """
    job_number_pattern: Pattern = re.compile(r"\b(\d{6,8})\b")
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
    date_due_pattern = re.compile(
        r"(?i)(DUE|BACK)[_/\s-](\d{1,2}[-.what is 0o666]\d{1,2})"
    )
    date_due_matches = date_due_pattern.search(file)
    date_due = date_due_matches.group(2) if date_due_matches else ""
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
    for file in directory.iterdir():
        if file.is_file():
            mime_type, _ = mimetypes.guess_type(str(file))
            if mime_type and mime_type is not None:
                if (
                    mime_type.startswith("audio/")
                    or mime_type.startswith("video/")
                    or mime_type == "application/octet-stream"
                ):
                    media_files.append(file)
    return sorted(media_files)


def truncate(num: float, dp: int) -> float:
    """
    Truncate a float number to the specified number of decimal places.

    Arguments:
        num: The float number to be truncated.
        dp: The number of decimal places to truncate to.

    Returns:
        A float number truncated to dp decimal places.
    """
    num_str = str(num)
    return float(math.trunc(Decimal(num_str) * Decimal(10**dp)) / Decimal(10**dp))


def sec_to_min(seconds: float) -> float:
    """
    Convert duration in seconds to minutes.

    Arguments:
        seconds: The duration in seconds.

    Returns:
        The duration in minutes, rounded to two decimal places.
    """
    minutes = (seconds // 60) + ((seconds % 60) / 60)
    return truncate(minutes, 2)


def get_media_duration(media_file: Path | str) -> float:
    """
    Get the duration of an audio.

    Arguments:
        media_file: Path to the media file.

    Returns:
        The duration of the media file in minutes.
    """
    with audio_open(media_file) as f:
        duration = f.duration
    return sec_to_min(duration)


# def format_date(date_str: str, date_fmt: str):
#     """
#     Convert month.day ('%m.%d') string to full date string.
#
#     Arguments:
#         date_str: String with format of '%m.%d' date format.
#         date_fmt: Date format string.
#
#     Returns:
#         A date string.
#
#     """
#     try:
#         full_date_string = f"{date_str}.{date.today().year}"
#         date_obj = datetime.strptime(full_date_string, "%m.%d.%Y")
#         return date_obj.strftime(date_fmt)
#     except ValueError:
#         return ""
def format_date(date_str: str, date_fmt: str) -> str:
    """
    Convert a month.day ('%m.%d') string to a full date string.

    Args:
        date_str (str): A string in the format '%m.%d'.
        date_fmt (str): The desired date format string.

    Returns:
        A string representing the date in the given format,
        or an empty string if the input date_str is invalid.
    """
    try:
        year = datetime.now().year
        full_date_str = f"{date_str}.{year}"
        date_obj = datetime.strptime(full_date_str, "%m.%d.%Y")
        return date_obj.strftime(date_fmt)
    except ValueError:
        return ""


def str_to_date(date_string: str, date_fmt):
    return datetime.strptime(date_string, date_fmt)


std = str_to_date


def date_to_str(date_obj, date_fmt):
    return date_obj.strftime(date_fmt)


dts = date_to_str


def parse_quantity(
    quantity: str | float | int, total_quantity: str | float | int
) -> float:
    """
    Parses a quantity value provided as a float, integer, or string fraction.

    If the input quantity is a float or integer, it is simply truncated to two decimal places.

    If the input quantity is a string, it is first converted to a fraction using the built-in
    'fractions.Fraction' class. If the resulting fraction is greater than or equal to 1, it is
    simply truncated to two decimal places. If the fraction is less than 1, the function
    requires a 'total_quantity' parameter, which is used to calculate the equivalent quantity
    value as a float.

    Arguments:
        quantity: The quantity value to parse, provided as a float, integer, or string fraction.
        total_quantity: The total quantity value to use for calculating string fractions less
                        than 1. Required when the input quantity is a string fraction less than 1.

    Returns:
        The parsed quantity value as a float, truncated to two decimal places.

    Raises:
        TypeError: If the quantity argument is empty or the input type is invalid.
                   If the input quantity is a string fraction less than 1 and total_quantity
                   is not provided.
    """
    if not quantity:
        raise TypeError("Quantity is required")

    if isinstance(quantity, (float, int)):
        return truncate(quantity, 2)

    if isinstance(quantity, str):
        try:
            f = Fraction(quantity)
            if f > 1:
                return truncate(float(quantity), 2)
            else:
                if not total_quantity:
                    raise TypeError("Total quantity required")
                else:
                    return truncate(float(f) * float(total_quantity), 2)
        except ValueError:
            # logger
            print("Valid fraction, int, float, str required")

    raise TypeError("Valid fraction, int, float, str required")


def rel_date(days: int):
    """
    Get relative date from today

    Args:
        days: number of days from/before today eg, 1 or -5

    Return:
        date object
    """
    return datetime.today().date() + timedelta(days=days)


class CSVTextBuilder:
    """
    Class to build a CSV text file from a list of dictionaries.
    """

    def __init__(self):
        self.csv_string = []

    def write(self, row):
        self.csv_string.append(row)


def dict_to_csv(dic, headers=[]):
    """
    Convert a dictionary to a CSV string.

    Arguments:
        dic: Dictionary to convert to a CSV string.

    Returns:
        A CSV string.
    """
    csv_builder = CSVTextBuilder()

    writer = csv.DictWriter(csv_builder, fieldnames=headers)
    if headers:
        writer.writeheader()
    for row in dic:
        writer.writerow(row)
    return "".join(csv_builder.csv_string)


def list_of_tuples_to_csv(l):
    """
    Convert a list of tuples to a CSV string.

    Arguments:
        l: List of tuples to convert to a CSV string.

    Returns:
        A CSV string.
    """
    csv_builder = CSVTextBuilder()
    fieldnames = l[0]
    writer = csv.writer(csv_builder)
    writer.writerow(fieldnames)

    for obj in l[1]:
        writer.writerow(obj)

    return "".join(csv_builder.csv_string)


def list_of_rows_to_csv(
    rows: List[object], headers: List[str] = [], omit: List[str] = []
) -> str:
    """
    Convert a list of rows to a CSV byte string.

    Arguments:
        rows: List of rows to convert to a CSV string.
        headers: List of column headers.
        omit: List of columns to omit.

    Returns:
        A CSV byte string.
    """
    dicts = [
        {k: getattr(row, k) for k in row.__dict__ if k != "_sa_instance_state"}
        for row in rows
    ]
    if omit:
        dicts = [{k: v for k, v in d.items() if k not in omit} for d in dicts]
    if headers:
        dicts = [
            dict(sorted(d.items(), key=lambda t: headers.index(t[0]))) for d in dicts
        ]

    csv_builder = CSVTextBuilder()
    writer = csv.writer(csv_builder)
    if headers:
        writer.writerow(headers)
    for d in dicts:
        writer.writerow(d.values())
    return "".join(csv_builder.csv_string)


def csv_from_docx(docx_path: str) -> str:
    """
    Convert docx file with table to csv.

    Arguments:
        docx_path: Path to docx file.

    Returns:
        CSV string
    """
    try:
        docx_file = docx.Document(docx_path)
    except docx.opc.exceptions.PackageNotFoundError:
        print("Docx file not found")
        return ""
    csv_file = StringIO()
    csv_writer = csv.writer(csv_file)
    for table in docx_file.tables:
        for row in table.rows:
            # csv_writer.writerow(list(map(lambda cell: cell.text, row.cells)))
            csv_writer.writerow([cell.text for cell in row.cells])
    return csv_file.getvalue()


def is_valid_email(text):
    """
    Check if a string is a valid email address.

    Arguments:
        text: String to check.

    Retuns:
        True if the string is a valid email address, otherwise False.
    """
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", text))


# ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$


def is_valid_string(text):
    """
    Check if a string is a valid string.

    Arguments:
        text: String to check.

    Returns:
        True if the string is a valid string, otherwise False.
    """
    if isinstance(text, (str, bytes)):
        return bool(re.match(r"^.+$", text))
    return False


def is_valid_float(text):
    """
    Check if a string is a valid float.

    Arguements:
        text: String to check.
    Returns:
        True if the string is a valid float, otherwise False.
    """
    return bool(re.match(r"^[-+]?[0-9]*\.?[0-9]+$", text))


def is_valid_yes_no(text):
    """
    Check if a string is a valid yes or no.

    Arguments:
        text: String to check.
    Retuns:
        True if the string is a valid yes or no, otherwise False.
    """
    return bool(re.match(r"(?i)^[YyNn](?:es|o)?$", text))


def is_in_choices(text, choices):
    """
    Check if a string is in a list of choices.

    Arguments:
        text: String to check.
        choices: List of choices.
    Returs:
        True if the string is in the choices, otherwise False.
    """
    return text.strip() in choices


def is_work_choices(text):
    """
    Check if a string is in a list of choices.

    Arguments:
        text: String to check.
    Returs:
        True if the string is in the choices, otherwise False.
    """
    WORK_CHOICES = ["Normal", "Interpreted", "Expedite"]
    return is_in_choices(text, WORK_CHOICES)


def is_template_choices(text):
    """
    Check if a string is in a list of choices.

    Arguments:
        text: String to check.
    Returs:
        True if the string is in the choices, otherwise False.
    """
    TEMPLATE_CHOICES = ["nd", "nh", "ne", "zd", "zh", "ze", "zdi", "tt", "me"]
    return is_in_choices(text, TEMPLATE_CHOICES)


def is_valid_file(text):
    """
    Check if a string is a valid file.

    Arguments:
        text: String to check.

    Retuns:
        True if the string is a valid file, otherwise False.
    """
    path = Path(text)
    return all([path.exists(), not path.is_dir()])


def is_valid_date(text):
    """
    Check if a string is a valid date.

    Arguments:
        text: String to check.
    Retuns:
        True if the string is a valid date, otherwise False.
    """
    match = re.match(r"([0-9]{2,4}[./-]){2}[0-9]{2,4}", text)
    return all([match])


def is_gt_0(text):
    """
    Check if a string is greater than zero.

    Arguments:
        text: String to check.
    Retuns:
        True if the string is greater than zero, otherwise False.
    """
    if text != "":
        return (int(text)) > 0


def MyValidator(func, error_mesage, mve=True):
    """
    Decorator to validate input.

    Arguments:
        func: Function to validate input.
        error_mesage: Error message to display if input is invalid.
        mve: move cursor to end of line if input is invalid.
        Returns:
            The decorated function.
    """
    return Validator.from_callable(func, error_mesage, move_cursor_to_end=mve)


name_validator = MyValidator(is_valid_string, "Invalid name")
email_validator = MyValidator(is_valid_email, "Invalid email")
float_validator = MyValidator(is_valid_float, "Invalid rate")
job_file_validator = MyValidator(is_valid_file, "File does not exist")
yes_no_validator = MyValidator(
    is_valid_yes_no, "Invalid input, expects [Y, Yes, N, No]"
)
work_validator = MyValidator(
    is_work_choices, "Valid choices [Normal, Interpreted, Expedite]"
)
template_type_validator = MyValidator(
    is_template_choices, "Valid choices [nd, nh, ne, zd, zh, ze, zdi, tt, me]"
)
date_validator = MyValidator(is_valid_date, "Invalid date")
gt0_validator = MyValidator(is_gt_0, "Is less than 0")
