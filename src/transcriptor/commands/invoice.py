from datetime import date

import click

from transcriptor.api import create_invoice
from transcriptor.methods import DATE_FMT

TODAY = date.today().strftime(DATE_FMT)


@click.group()
def cli(**kwargs):
    "Invoice actions"
    pass


@cli.command()
@click.option("-c", "--client", required=True, help="Specify client", prompt=True)
@click.option("-f", "--date-from", required=True, help="Specify date from", prompt="Include jobs from [YYYY-MM-DD]")
@click.option("-t", "--date-to", default=TODAY, help="Specify date to", prompt="Include jobs to  ")
def create(client=None, date_from=None, date_to=None, **kwargs):
    """Create client invoice"""
    create_invoice(client_name=client, date_from=date_from, date_to=date_to)
