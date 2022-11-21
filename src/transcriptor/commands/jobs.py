from datetime import date

import click
from sqlalchemy import select

from transcriptor.base import Transcriptor
from transcriptor.models import ClientModel, JobModel
from transcriptor.utils import format_date, parse_due_date
from transcriptor.view import ConsoleView

app = Transcriptor()

DATE_FMT = app.config.date_format
TODAY = date.today().strftime(DATE_FMT)


def due_date_cb() -> str:
    rdd = parse_due_date(click.get_current_context().params["file"])
    return format_date(rdd, DATE_FMT)


@click.group()
def cli(**kwargs):
    """Job actions."""
    pass


@cli.command()
@click.option(
    "-f", "--file", type=click.Path(exists=True), required=True, is_eager=True
)
@click.option(
    "-c",
    "--client",
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
def create(file, client, date_received, date_due, **kwargs):
    """Create job"""
    with app.api.session as session:
        # TODO Handle multiple clients with almost same name
        client = session.execute(
            select(ClientModel).filter(ClientModel.name.like(f"%{client}%"))
        ).scalar_one()

        app.add_job(
            client=client, job_file=file, date_received=date_received, date_due=date_due
        )


@cli.command()
def list(**kwargs):
    jobs = app.api.execute_sql("SELECT * FROM Jobs").fetchall()
    if jobs:
        cols = tuple(jobs[0]._asdict().keys())
        rows = jobs
        ConsoleView().vertical_table(cols, rows, headers=cols)


@cli.command()
@click.argument("id")
def delete(id, **kwargs):
    with app.api.session as session:
        j = session.execute(select(JobModel).filter_by(id=f"{id}")).scalar_one()
        session.delete(j)
        session.commit()
