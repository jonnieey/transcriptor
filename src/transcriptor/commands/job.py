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
    if date_received == None:
        date_received = date.today()
    else:
        date_received = get_date_received(date_received)

    if date_due == None:
        date_due = input("Enter date due: ")
    else:
        date_due = get_date_due(date_due)

    client_obj = get_client_object(client)
    create_job(file, date_received, date_due, client_obj)


@cli.command()
@click.option("-c", "--client", help="Specify client")
def list(client=None, **kwargs):
    """List client's jobs"""
    if client is None:
        clients = list_clients()
        choice = int(input("Select client: "))
        client = clients[choice].name
        jobs_table = list_client_jobs(client)
        print(jobs_table)
    elif client:
        jobs_table = list_client_jobs(client)
        if jobs_table is not None:
            print(jobs_table)
        else:
            clients = list_clients()
            choice = int(input("Select client: "))
            client = clients[choice].name
            jobs_table = list_client_jobs(client)
            print(jobs_table)
