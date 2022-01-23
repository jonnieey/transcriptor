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
@click.option(
    "-f",
    "--from",
    "from_",
    required=True,
    type=click.DateTime(formats=[DATE_FMT]),
    prompt="Include jobs from",
    help="Specify date from",
)
@click.option(
    "-t",
    "--to",
    default=TODAY,
    type=click.DateTime(formats=[DATE_FMT]),
    prompt="Include jobs to",
    help="Specify date to",
)
@click.option("-d", "--as-docx", is_flag=True, help="Create invoice as docx")
def create(client=None, from_=None, to=None, as_docx=None, **kwargs):
    """Create client invoice"""
    date_from = from_.date()
    date_to = to.date()
    create_invoice(
        client_name=client, date_from=date_from, date_to=date_to, as_docx=as_docx
    )
