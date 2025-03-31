import mimetypes
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Tuple,
    Union,
)

import docx  # type: ignore
from audioread import audio_open  # type: ignore
from bs4.element import Tag
from jinja2 import (
    ChoiceLoader,
    Environment,
    FileSystemLoader,
    PackageLoader,
    StrictUndefined,
    select_autoescape,
)
from markdownify import MarkdownConverter  # type: ignore
from prompt_toolkit.validation import Validator
from weasyprint import HTML  # type: ignore

from transcriptor.models import Invoice, SummaryInvoice


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


def sc(s: str) -> str:
    return convert_case(s, r"[ -]", "_")


def nc(s: str) -> str:
    return convert_case(s, r"[-_]", " ")


def kc(s):
    return convert_case(s, r"[ _]", "-")


def tc(s: str) -> str:
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


def get_media_files(directory: Path) -> Generator[Path, None, None]:
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


def next_non_existent_file(filename: Path | str) -> Path:
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


def round_up(number: float) -> float:
    if number % 0.5 == 0:
        return number
    else:
        return number + 0.5 - (number % 0.5)


def parse_conditions_as_dict(condition_strings: List[str]) -> Dict[str, str]:
    """
    input = ['name=anderson', 'id<=1', 'amount>0']
    output = {'name': 'anderson', 'id': 1, 'amount': '0' }
    """
    conditions_dict = {}
    for condition_string in condition_strings:
        field, value = condition_string.split("=")
        conditions_dict[field] = value
    return conditions_dict


def parse_conditions(
    condition_strings: List[str],
) -> Dict[str, Union[List[Tuple[str, str]], List[Tuple[str, int]]]]:
    """
    Parses a list of condition strings and returns a dictionary.

    Args:
        condition_strings: A list of strings representing conditions like "id<=1", "amount>0".

    Returns:
        A dictionary where keys are field names (e.g., "id", "amount") and values are
        lists of tuples, each tuple containing an operator and a value.
        For example: {"id": [("<=", 1)], "amount": [(">", 0), ("<", 10)]}
    """
    conditions_dict: Dict[str, List[Tuple[str, Any]]] = {}
    operators = {
        "<=": "<=",
        ">=": ">=",
        "!=": "!=",
        "<": "<",
        ">": ">",
        "==": "=",
        "=": "==",
        "~": "~",
    }

    for condition_str in condition_strings:
        parsed = False
        for op_symbol, op_name in operators.items():
            if op_symbol in condition_str:
                parts = condition_str.split(op_symbol, 1)  # Split only once
                if len(parts) == 2:
                    field = parts[0].strip()
                    value_str = parts[1].strip()
                    try:
                        value = type_convert(
                            value_str
                        )  # Try to convert value to int or float, otherwise keep as string
                        if field:  # Ensure field name is not empty
                            if field not in conditions_dict:
                                conditions_dict[field] = []
                            conditions_dict[field].append((op_name, value))
                            parsed = True
                            break  # Stop checking operators after finding one
                    except ValueError:
                        print(
                            f"Warning: Could not convert value '{value_str}' to a number for condition '{condition_str}'. Treating as string."
                        )
                        if field:
                            if field not in conditions_dict:
                                conditions_dict[field] = []
                            conditions_dict[field].append(
                                (op_name, value_str)
                            )
                            parsed = True
                            break
        if not parsed:
            print(
                f"Warning: Could not parse condition string: '{condition_str}'. Ensure it is in the format 'field[operator]value'."
            )

    return conditions_dict


def type_convert(value_str: str) -> Union[str, int, float]:
    """
    Attempts to convert a string to an int or float. If it fails, returns the string as is.
    """
    try:
        return int(value_str)
    except ValueError:
        try:
            return float(value_str)
        except ValueError:
            return value_str  # Return as string if not int or float


job_number_pattern = re.compile(r"\b(\d{6,8})\b")


def extract_job_number(file: str) -> str:
    """
    Get job number from path-like string.

    Arguments:
        file: Path-like string

    Returns:
        String (6-8 digit number string) ex. 534223.
    """
    job_number_matches = job_number_pattern.search(file)

    return job_number_matches.group(1) if job_number_matches else ""


def seconds_to_minutes(seconds: float) -> float:
    minutes = (seconds // 60) + ((seconds % 60) / 60)
    return round_up(minutes)


def get_media_duration(media_file: Path) -> float:
    with audio_open(media_file) as mf:
        duration = mf.duration
    return seconds_to_minutes(duration)


def is_file(text: str) -> bool:
    path = Path(text.strip("'").strip('"'))
    return path.is_file()


def is_positive_number(text: str) -> bool:
    try:
        return Decimal(text) > 0
    except (InvalidOperation, TypeError):
        return False


def is_valid_date(text: str) -> bool:
    return bool(re.match(r"([0-9]{2,4}[./-]){2}[0-9]{2,4}", text))


def is_valid_yes_no(text: str) -> bool:
    return bool(re.match(r"(?i)^[YyNn](?:es|o)?$", text))


def is_valid_job_type(text: str) -> bool:
    return bool(re.match(r"(?i)^(?:Normal|Interpreted|Expedite)$", text))


template_mapping = {
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


def is_valid_template(text: str):
    if text.lower() in template_mapping:
        return True
    else:
        return False


def ValidatorWrapper(
    func: Callable, error_message: str, mve: bool = True
) -> Validator:
    return Validator.from_callable(
        func, error_message, move_cursor_to_end=mve
    )


file_validator = ValidatorWrapper(is_file, "File does not exist")
positive_number_validator = ValidatorWrapper(
    is_positive_number, "Must be greater than zero"
)
date_validator = ValidatorWrapper(is_valid_date, "Invalid date")
yes_no_validator = ValidatorWrapper(
    is_valid_yes_no, "Invalid input, expects [Y, Yes, N, No]"
)
job_type_validator = ValidatorWrapper(
    is_valid_job_type,
    "Invalid job type, expects [Normal Interpreted Expedite]",
)
template_validator = ValidatorWrapper(
    is_valid_template,
    f"Invalid template name, expects {','.join(list(template_mapping.keys()))}",
)


def _init_jinja_env(custom_templates_dir: Optional[Path]) -> Environment:
    loaders = []
    if custom_templates_dir is not None:
        loaders.append(FileSystemLoader(custom_templates_dir))
    loaders.append(PackageLoader("transcriptor", "invoice_templates"))  # type: ignore
    loader = ChoiceLoader(loaders)
    return Environment(
        loader=loader,
        autoescape=select_autoescape(),
        undefined=StrictUndefined,
    )


def htmlstr_to_pdf(htmlstr: str, output_path: Path) -> Optional[bytes]:
    return HTML(string=htmlstr).write_pdf(output_path)


def render_invoice(
    invoice: Invoice,
    custom_templates_dir: Optional[Path] = None,
    template_name: Optional[str] = None,
) -> str:
    if template_name is None:
        template_name = "invoice_default.html"
    template = _init_jinja_env(custom_templates_dir).get_template(
        template_name
    )
    return template.render(invoice=invoice)


def render_summary_invoice(
    summary_invoice: SummaryInvoice,
    custom_templates_dir: Optional[Path] = None,
    template_name: Optional[str] = None,
) -> str:
    if template_name is None:
        template_name = "summary_invoice.html"
    template = _init_jinja_env(custom_templates_dir).get_template(
        template_name
    )
    return template.render(summary_invoice=summary_invoice)


def write_pdf(
    invoice,
    output_path: Path,
    custom_templates_dir: Optional[Path],
    template_name=Optional[str],
) -> Optional[bytes]:
    return htmlstr_to_pdf(
        render_invoice(invoice, custom_templates_dir, template_name),
        output_path,
    )


class MDConverter(MarkdownConverter):
    """
    Converter for Markdown to HTML
    """

    def convert_tr(self, el: Tag, text: str, convert_as_inline: bool) -> str:
        return super().convert_tr(el, text, convert_as_inline) + "\n"


def md(html: str, **options) -> str:
    """
    Convert Markdown to HTML
    """
    return MDConverter(**options).convert(html)


def html_to_md(html: str) -> str:
    markdown = md(html)
    md_table = markdown[markdown.find("![]()") + 5 :]
    md_table = re.sub(r"\n{2,}", "\n\n", md_table)
    return md_table


def invoice_template_themes():
    invoice_template_dir = Path(__file__).parent / "invoice_templates"
    template_themes = []
    for invoice_file in invoice_template_dir.iterdir():
        if invoice_file.stem.startswith("invoice_"):
            template_themes.append(invoice_file.stem.replace("invoice_", ""))
    return template_themes


def extract_table_data_from_docx(docx_path: str) -> List[List[str]]:
    try:

        docx_file = docx.Document(docx_path)
    except ImportError:
        print("docx library not installed")

    except docx.opc.exceptions.PackageNotFoundError:
        print("Docx file not found")
        return []

    table_data: List[List[str]] = []
    for table in docx_file.tables:
        table_data.extend(
            [cell.text for cell in row.cells] for row in table.rows
        )
    return table_data


def to_date_object(iterable: List[str], date_fmt: str) -> Tuple[date, ...]:
    return tuple(
        str_to_date(date_str.strip(), date_fmt).date()
        for date_str in iterable
    )


def extract_date_due(file: str) -> str:
    date_due_pattern = re.compile(
        r"(?i)(DUE|BACK)[_/\s-](\d{1,2}[-./]\d{1,2})"
    )
    date_due_matches = date_due_pattern.search(file)
    return date_due_matches[2] if date_due_matches else ""


def month_day_to_date(
    date_str: str, date_fmt: str = "%Y-%m-%d", year: str = ""
) -> str:
    """
    Convert a month.day ('%m.%d') string to a full date string.

    Args:
        date_str (str): A string in the format '%m.%d'.
        date_fmt (str): The desired date format string.
        year (str): The year to append to the date string.

    Returns:
        A string representing the date in the given format,
        or an empty string if the input date_str is invalid.
    """
    try:
        if not year:
            current_year = f"{datetime.now().year}"
            year = current_year
        date_str = f"{date_str}.{year}"
        date_obj = datetime.strptime(date_str, "%m.%d.%Y")
        return date_obj.strftime(date_fmt)
    except ValueError:
        return ""


def parse_sql_clause(sql_clause, split_by):
    condition_list = sql_clause.split(split_by)
    condition_dict = {}

    for condition in condition_list:
        parts = condition.split("=")
        if len(parts) != 2:
            continue
        column, value = parts
        column = column.strip()
        value = value.strip()
        if value.startswith(("'", '"')) and value.endswith(("'", '"')):
            value = value[1:-1]
        condition_dict[column] = value

    return condition_dict


def parse_sql_update_query(sql_query):
    set_clause_start = sql_query.upper().find("SET") + len("SET")
    where_clause_start = sql_query.upper().find("WHERE")

    if where_clause_start == -1:
        where_clause_start = len(sql_query)

    set_clause = sql_query[set_clause_start:where_clause_start].strip()
    set_assignments = parse_sql_clause(set_clause, ",")

    where_assignments = {}
    if where_clause_start < len(sql_query):
        where_clause = sql_query[where_clause_start + len("WHERE") :].strip()
        where_assignments = parse_sql_clause(where_clause, "AND")

    return set_assignments, where_assignments


def get_version():
    try:
        init_file_path = Path(__file__).parent / "__init__.py"
        with open(init_file_path, "r") as fd:
            init_content = fd.read()

            version_match = re.search(
                r"^__version__\s*=\s*[\"']([^\"']*)[\"']",
                init_content,
                re.MULTILINE,
            )

            if version_match:
                return version_match.group(1)
            else:
                raise ValueError("Could not determine version")
    except FileNotFoundError:
        raise FileNotFoundError(f"__init__.py not found at {init_file_path}")
    except ValueError as e:
        raise ValueError(f"Error determining version: {e}")


if __name__ == "__main__":
    # stmt = "SET amount_paid=2222 WHERE client_id=1 AND date_received='2023-04-22' AND job_number='JOB001'"
    # s, w = parse_sql_update_query(stmt)
    # print(s, w)
    print(get_version())
