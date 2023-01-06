import logging
from datetime import date

import click

from transcriptor.base import Transcriptor
from transcriptor.models import ClientModel, RatesModel
from transcriptor.utils import *
from transcriptor.view import ConsoleView

logger = logging.getLogger(__name__)

app = Transcriptor()

DATE_FMT = app.config.date_format
TODAY = date.today().strftime(DATE_FMT)


def due_date_cb() -> str:
    rdd = parse_due_date(click.get_current_context().params["job_file"])
    return format_date(rdd, DATE_FMT)


@click.group()
def cli(**kwargs):
    """Job actions."""
    pass


@cli.command()
@click.option(
    "-f", "--job-file", type=click.Path(exists=True), required=True, is_eager=True
)
@click.option(
    "-c",
    "--client-name",
    prompt="Enter client's name",
    help="Specify client name",
)
@click.option(
    "-r",
    "--date-received",
    default=TODAY,
    required=True,
    prompt="Enter date job received",
    help="Specify date job received fmt: YYYY-MM-DD",
)
@click.option(
    "-d",
    "--date-due",
    required=True,
    prompt="Enter date job due",
    is_eager=True,
    default=due_date_cb,
    help="Specify due date fmt: YYYY-MM-DD",
)
def create(job_file, client_name, date_received, date_due, **kwargs):
    """Create job"""

    def add_job_cb(
        media_file: str,
        client: ClientModel,
        rates: RatesModel,
        date_received: str,
        job_num: str,
        job_dir: str | Path,
    ):

        click.echo(media_file)
        work_on_file = click.prompt(
            "Work on this file",
            type=click.Choice(["Y", "N"], case_sensitive=False),
            show_choices=True,
        )
        if work_on_file.lower() == "y":
            job_type = click.prompt(
                "Specify job type",
                type=click.Choice(
                    ["Normal", "Interpreted", "Expedite"], case_sensitive=False
                ),
                show_choices=True,
            )
            total_quantity = get_media_duration(media_file)
            quantity = click.prompt("Enter quantity of task", default=total_quantity)
            job_template = click.prompt(
                "Specify template type",
                type=click.Choice(
                    ["nd", "nh", "ne", "zd", "zh", "ze", "zdi", "tt", "me"],
                    case_sensitive=False,
                ),
                show_choices=True,
            )
            note = input("Notes: ")
            job_rate = rates.__dict__.get(job_type, 0.40)

            job_dict = {
                "client_id": client.id,
                "date_received": date_received,
                "job_number": job_num,
                "job_type": job_type,
                "total_quantity": total_quantity,
                "job_rate": job_rate,
                "quantity": quantity,
                "date_due": date_due,
                "job_path": str(job_dir),
                "note": note,
            }
            job = app.api.create_job(**job_dict)
            return job

    app.add_job(
        add_job_cb=add_job_cb,
        client_name=client_name,
        job_file=job_file,
        date_received=date_received,
        date_due=date_due,
    )


@cli.command()
@click.option("-c", "--client-id", type=int, help="Specify client id")
@click.option("-R", "--date-received", type=str, help="Specify date received")
@click.option("-n", "--job-number", type=str, help="Specify job number")
@click.option(
    "-t",
    "--job-type",
    type=click.Choice(["Normal", "Interpreted", "Expedite"], case_sensitive=False),
    help="Specify job type",
)
@click.option(
    "-s",
    "--status",
    type=click.Choice(["Done", "Pending"], case_sensitive=False),
    help="Specify job status",
)
@click.option("-D", "--date-due", type=str, help="Specify date due")
@click.option("-q", "--quantity", type=float, help="Specify job quantity")
@click.option("-r", "--job-rate", type=float, help="Specify job rate")
@click.option("-S", "--date-submitted", type=str, help="Specify date submitted")
@click.option("-a", "--amount-paid", type=float, help="Specify amount paid")
@click.option("-N", "--note", type=str, help="Specify note")
def list(**kwargs):
    """List all jobs"""
    attr = {k: v for k, v in kwargs.items() if v is not None}
    jobs = app.api.list_jobs(attributes=attr)
    total_amount, total_amount_paid = app.api.get_jobs_scalars_total(jobs)
    total_dict = {"total_amount": total_amount, "total_amount_paid": total_amount_paid}
    ConsoleView().print_job_table(jobs, **total_dict)


@cli.command()
# values to edit
@click.argument("job_id")
@click.option("-c", "--client-id", type=int, help="Specify client id")
@click.option("-R", "--date-received", type=str, help="Specify date received")
@click.option("-n", "--job-number", type=str, help="Specify job number")
@click.option(
    "-t",
    "--job-type",
    type=click.Choice(["Normal", "Interpreted", "Expedite"], case_sensitive=False),
    help="Specify job type",
)
@click.option(
    "-s",
    "--status",
    type=click.Choice(["Done", "Pending"], case_sensitive=False),
    help="Specify job status",
)
@click.option("-D", "--date-due", type=str, help="Specify date due")
@click.option("-q", "--quantity", type=float, help="Specify job quantity")
@click.option("-r", "--job-rate", type=float, help="Specify job rate")
@click.option("-S", "--date-submitted", type=str, help="Specify date submitted")
@click.option("-a", "--amount-paid", type=float, help="Specify amount paid")
@click.option("-N", "--note", type=str, help="Specify note")
def edit(**kwargs):
    """Edit job attributes"""
    app.api.edit_job(**kwargs)


@cli.command()
@click.argument("job_id")
def delete(job_id, **kwargs):
    """Delete job from database"""
    app.api.delete_job(job_id)
