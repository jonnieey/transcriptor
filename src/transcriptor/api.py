import os
import shutil
import sys
import zipfile
from datetime import date
from pathlib import Path
from typing import Optional, Union

import click
# from beautifultable import BeautifulTable
from rich.console import Console
from rich.table import Table

from transcriptor.client import Client
from transcriptor.client_list import ClientList
from transcriptor.methods import (
    create_client,
    create_task,
    filter_jobs_by_date,
    generate_invoice_docx,
    generate_invoice_pdf,
    get_clients,
    get_jobs,
    get_template_file,
    save_client,
    save_job_to_file,
    settings,
)
from transcriptor.profile import Profile
from transcriptor.utils import (
    deformat_date,
    get_media_duration,
    get_media_files,
    get_quantity,
    parse_job_due_date,
    parse_job_number,
)

CLIENTS_FOLDER, WORKS_FOLDER, JOBS_FOLDER, CONFIG_FOLDER, RESOURCES_FOLDER = (
    settings.clients_folder,
    settings.works_folder,
    settings.jobs_folder,
    settings.config_folder,
    settings.resources_folder,
)


def add_client(
    name: str,
    email: str,
    clients_folder: Optional[Path] = CLIENTS_FOLDER,
) -> None:
    new_client = create_client(name=name, email=email)
    clients = get_clients(CLIENTS_FOLDER)
    client_name = ""
    if clients:
        for client in clients:
            if client.name == new_client.name:
                sys.exit("Client already exists")
            else:
                continue
    save_client(client=new_client, clients_folder=clients_folder)
    client_name = new_client.name

    resources_folder = RESOURCES_FOLDER
    assert resources_folder is not None

    client_resourse_folder = resources_folder / client_name
    shutil.copytree(Path(__file__).parent / "resources/", client_resourse_folder)


def get_client_object(client_name: str) -> Client:
    clients = get_clients(CLIENTS_FOLDER)

    for client_obj in clients:
        if client_name.lower() in client_obj.name.lower():
            client = client_obj
            return client
        else:
            continue

    sys.exit("Client does not exist")


def create_job(
    zip_file: Optional[Path],
    date_received: str,
    date_due: str,
    client: Client,
    note: str = "",
) -> None:
    job_number = parse_job_number(zip_file)
    if date_due is None:
        date_due = parse_job_due_date(zip_file)

    job_folder_stem = "%s-%s_DUE_%s" % (date_received, job_number, date_due)
    works_folder = WORKS_FOLDER
    assert works_folder is not None
    job_folder = works_folder / client.name / job_folder_stem

    if not job_folder.exists():
        job_folder.mkdir(parents=True, exist_ok=True)

    try:
        if os.environ["TRANSCRIPTOR_TEST"] == "1":
            new_zip_file = shutil.copy2(zip_file, job_folder)
        else:
            new_zip_file = shutil.move(zip_file, job_folder)
    except (shutil.SameFileError, shutil.Error):
        new_zip_file = zip_file
    try:
        zipfile.ZipFile(new_zip_file).extractall(job_folder)
    except Exception as error:
        sys.exit(error)

    tasks = []

    media_files = get_media_files(job_folder)
    for media_file in media_files:

        click.echo(media_file)
        work_on_file = click.prompt(
            "Work on this file",
            type=click.Choice(["Y", "N"], case_sensitive=False),
            show_choices=True,
        )
        if work_on_file.lower() == "y":
            total_quantity = get_media_duration(media_file)
            job_type = click.prompt(
                "Specify job type",
                type=click.Choice(
                    ["Normal", "Interpreted", "Expedite"], case_sensitive=False
                ),
                show_choices=True,
            )
            quantity = get_quantity(
                click.prompt("Enter quantity of task", default=str(total_quantity)),
                total_quantity=total_quantity,
            )
            task = create_task(
                date_received=date_received,
                job_number=job_number,
                job_type=job_type,
                total_quantity=total_quantity,
                quantity=quantity,
                date_due=date_due,
                job_path=job_folder,
                note=note,
            )
            task.amount = round(task.job_rate * task.quantity, 0)
            tasks.append(task)
            template_type = click.prompt(
                "Enter template type",
                type=click.Choice(
                    ["nd", "nh", "ne", "zd", "zh", "ze", "tt", "di", "me"],
                    case_sensitive=False,
                ),
                show_choices=True,
            )
            template_file = get_template_file(client.name, template_type)
            shutil.copy2(
                template_file,
                "%s/%s"
                % (job_folder, "%s Due %s.doc" % (job_number, deformat_date(date_due))),
            )
        else:
            continue

    save_job_to_file(client, tasks, JOBS_FOLDER)


def print_clients(clients: list[Client]) -> None:
    headers = ["", "Name", "Email"]
    table = Table()

    [table.add_column(header=x) for x in headers]
    [table.add_row(str(idx + 1), c.name, c.email) for idx, c in enumerate(clients)]

    console = Console()
    console.print(table)


def print_table(
    headers: list[str],
    jobs: list[list[str]],
    amount: float,
    amount_paid: float,
    show_path: bool = False,
    filter_by: str = "",
    title: str = "",
) -> None:
    table = Table(title=title, show_footer=True)
    table.title_style = "red bold"
    [table.add_column(column.replace("_", " ").title()) for column in headers]

    for job in jobs:
        [table.add_row(*job)]

    table.columns[0].footer = "TOTALS"
    for column in table.columns:
        if column.header == "Amount":
            column.footer = str(amount)
        if column.header == "Amount Paid":
            column.footer = str(amount_paid)
        if column.header in [
            "Quantity",
            "Job Rate",
            "Total Quantity",
            "Amount Paid",
            "Amount",
        ]:
            column.justify = "right"
    if not show_path:
        # delete column containing header Job Path
        del table.columns[[_.header for _ in list(table.columns)].index("Job Path")]

    # Implement table sorter, filter
    table.row_styles = ["none", "dim"]
    console = Console()
    console.print(table)


def list_client_jobs(client_name: str, show_path=False, filter_by: str = "") -> None:
    raw_jobs = get_jobs(client_name)

    if not raw_jobs:
        sys.exit("No Jobs available")

    headers = raw_jobs.headers()
    client = raw_jobs.clients()[0].name
    amount = raw_jobs.amount()
    amount_paid = raw_jobs.amount_paid()
    jobs = sorted(
        [list(map(str, list(job.to_dict().values()))) for job in raw_jobs.jobs()]
    )
    print_table(
        headers,
        jobs,
        amount,
        amount_paid,
        show_path=show_path,
        filter_by=filter_by,
        title=client,
    )


def list_all_jobs(
    per_client: bool = False, show_path: bool = False, filter_by: str = ""
) -> None:
    raw_jobs = get_jobs()
    if not raw_jobs:
        sys.exit("No Jobs available")

    headers = raw_jobs.headers()
    if per_client:
        for client_job in raw_jobs:
            amount = client_job.amount()
            amount_paid = client_job.amount_paid()
            client = client_job.client
            jobs = sorted(
                [
                    list(map(str, list(job.to_dict().values())))
                    for job in client_job.jobs()
                ]
            )
            click.echo()

            print_table(
                headers,
                jobs,
                amount,
                amount_paid,
                show_path=show_path,
                filter_by=filter_by,
                title=client.name,
            )
    else:
        amount = raw_jobs.amount()
        amount_paid = raw_jobs.amount_paid()
        # jobs = raw_jobs.jobs()
        # TODO Refactor
        jobs = sorted(
            [list(map(str, list(job.to_dict().values()))) for job in raw_jobs.jobs()]
        )
        print_table(
            headers,
            jobs,
            amount,
            amount_paid,
            show_path=show_path,
            filter_by=filter_by,
            title="All Jobs",
        )


def get_profile(profile_file: Optional[Path] = None) -> Profile:
    try:
        profile = Profile.load(profile_file)
    except FileNotFoundError:
        profile = create_profile_interactively(profile_file)

    return profile


def check_value(value: str) -> Optional[str]:
    if not value.strip():
        raise click.UsageError("Cannot be empty")
    return value


def create_profile_interactively(profile_path: Optional[Path]) -> Profile:
    first_name = click.prompt("Enter your first name", value_proc=check_value)
    last_name = click.prompt("Enter your last name", value_proc=check_value)
    country = click.prompt("Enter your country", default="")
    area = click.prompt("Enter your area", default="")

    user_profile = {
        "first_name": first_name,
        "last_name": last_name,
        "area": area,
        "country": country,
    }
    profile = Profile(**user_profile)
    config_folder = CONFIG_FOLDER
    if isinstance(config_folder, Path):
        profile.save(config_folder / "profile.json")

    return profile


def create_invoice(
    client_name: str,
    date_from: Union[str, date],
    date_to: Union[str, date],
    as_docx: bool = False,
) -> None:
    client = get_client_object(client_name)
    raw_jobs = get_jobs(client_name)
    jobs = filter_jobs_by_date(
        key="date_submitted",
        date_from=date_from,
        date_to=date_to,
        jobs=raw_jobs.jobs(),
    )
    new_client_jobs = ClientList(
        client=client.to_dict(), jobs_list=[j.to_dict() for j in jobs]
    )
    assert CONFIG_FOLDER is not None
    profile = get_profile(CONFIG_FOLDER / "profile.json")
    amount = new_client_jobs.amount()
    if as_docx:
        generate_invoice_docx(
            client=client, jobs=jobs, amount=amount, user_profile=profile
        )
    else:
        generate_invoice_pdf(
            client=client, jobs=jobs, amount=amount, user_profile=profile
        )
