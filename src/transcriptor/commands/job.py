from datetime import date

import click

from transcriptor import *
from transcriptor.api import *
from transcriptor.methods import *

TODAY = date.today().strftime(DATE_FMT)


@click.group()
def cli(**kwargs):
    "Job actions"
    pass


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "-r",
    "--date-received",
    default=TODAY,
    help="Specify date job received fmt: YYYY-MM-DD",
)
@click.option("-d", "--date-due", help="Specify date job due fmt: YYYY-MM-DD")
@click.option("-c", "--client", help="Specify client", prompt=True)
def create(file, date_received=None, date_due=None, client=None, **kwargs):
    """Create job"""
    date_received = get_date_received(date_received)

    if date_due == None:
        date_due = get_date_due(click.prompt("Enter date due"))
    else:
        date_due = get_date_due(date_due)

    client_obj = get_client_object(client)
    create_job(file, date_received, date_due, client_obj)


@cli.command()
@click.option("-c", "--client", help="Specify client")
@click.option("-a", "--all", is_flag=True, help="Specify client")
@click.option("-s", "--per-client", is_flag=True, help="List job per client")
@click.option("-p", "--show-path", is_flag=True, help="List job per client")
def list(client=None, all=None, per_client=None, show_path=None, **kwargs):
    """List client's jobs"""
    if all is True:
        list_all_jobs(per_client=per_client, show_path=show_path)
        return

    if client is not None:
        list_client_jobs(client, show_path=show_path)
    else:
        client = click.prompt("Enter client's name")
        list_client_jobs(client, show_path=show_path)


@cli.command()
@click.option("-j", "--job_number", required=True, help="Specify job number")
@click.option("-c", "--client", help="Specify client")
@click.option("-r", "--date-received", help="Specify date job received fmt: YYYY-MM-DD")
@click.option("-d", "--date-due", help="Specify date job due fmt: YYYY-MM-DD")
@click.option("-s", "--status", help="Specify status of job")
@click.option("-a", "--amount_paid", type=float, help="Specify amount paid")
def update(**kwargs):
    """Update job"""
    d = {k: v for k, v in kwargs.items() if v is not None}
    update_job(kwargs["job_number"], d)
