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
@click.option("-c", "--client", help="Specify client")
def create(file, date_received=None, date_due=None, client=None, **kwargs):
    """Create job"""
    date_received = get_date_received(date_received)

    if date_due == None:
        date_due = get_date_due(click.prompt("Enter date due"))
    else:
        date_due = get_date_due(date_due)

    if client is None:
        clients_list = list_clients()
        choice = click.prompt("Select client", type=int)
        client_obj = clients_list[choice]
    else:
        client_obj = get_client_object(client)
    create_job(file, date_received, date_due, client_obj)


@cli.command()
@click.option("-c", "--client", help="Specify client")
@click.option("--all", is_flag=True, help="Specify client")
def list(client=None, all=None, **kwargs):
    """List client's jobs"""
    if all is True:
        list_all_jobs()
        return

    if client is not None:
        list_client_jobs(client)
    else:
        client = click.prompt("Enter client's name")
        list_client_jobs(client)


@cli.command()
@click.option("-j", "--job_number", required=True, help="Specify amount paid")
@click.option("-c", "--client", help="Specify client")
@click.option("-r", "--date-received", help="Specify date job received fmt: YYYY-MM-DD")
@click.option("-d", "--date-due", help="Specify date job due fmt: YYYY-MM-DD")
@click.option("-s", "--status", help="Specify status of job")
@click.option("-a", "--amount_paid", type=float, help="Specify amount paid")
def update(**kwargs):
    d = {k: v for k, v in kwargs.items() if v is not None}
    update_job(kwargs["job_number"], d)
