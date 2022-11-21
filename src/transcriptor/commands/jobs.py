from datetime import date

import click
from sqlalchemy import select

from transcriptor.base import Transcriptor
from transcriptor.models import ClientModel, JobModel, RatesModel
from transcriptor.utils import *
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

    def add_job_cb(media_file, client, rates, date_received, job_num, job_dir):
        do = input("Do work? [Y/N]: ")
        if do.upper() == "Y":

            total_quantity = get_media_duration(media_file)
            quantity = float(input("duration: "))
            job_type = input("Job type: ").lower()
            job_template = input("Job template: ")
            note = input("Notes: ")
            job_rate = rates.__dict__.get(job_type, 0.40)

            job_dict = {
                "client_id": client.id,
                "date_received": date_received,
                "job_number": job_num,
                "job_type": job_type,
                "total_quantity": total_quantity,
                # TODO implement job rate
                "job_rate": job_rate,
                "quantity": quantity,
                "date_due": date_due,
                "job_path": str(job_dir),
                "note": note,
            }
            job = app.api.create_job(**job_dict)
            return job

    with app.api.session as session:
        stmt = (
            select(ClientModel, RatesModel)
            .filter(ClientModel.name.like(f"%{client}%"))
            .join(RatesModel)
        )
        scalars = session.execute(stmt).all()
        # TODO Handle multiple clients with almost same name
        # Only one client found
        if len(scalars) == 1:
            client = scalars[0]._asdict()["ClientModel"]
            rates = scalars[0]._asdict()["RatesModel"]

            app.add_job(
                add_job_cb,
                client=client,
                rates=rates,
                job_file=file,
                date_received=date_received,
                date_due=date_due,
            )


@cli.command()
def list(**kwargs):
    stmt = str(
        select(ClientModel.name.label("Client Name"), JobModel).join(ClientModel)
    )
    jobs = app.api.execute_sql(stmt).fetchall()
    if jobs:
        cols = jobs[0]._asdict()
        cols.pop("client_id")
        rows = jobs
        ConsoleView().vertical_table(cols, rows, headers=cols)


@cli.command()
@click.argument("id")
def delete(id, **kwargs):
    with app.api.session as session:
        j = session.execute(select(JobModel).filter_by(id=f"{id}")).scalar_one()
        session.delete(j)
        session.commit()
