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


@click.group()
def cli(**kwargs):
    """Invoice actions."""
    pass


@cli.command()
@click.option("-c", "--client-id", type=int, required=True, help="Specify client id")
@click.option(
    "-s", "--period-start", type=int, required=True, help="Specify start of job period"
)
@click.option(
    "-e", "--period-end", type=int, required=True, help="Specify end of job period"
)
def create(client_id, period_start, period_end, **kwargs):
    app.create_invoice(
        client_id=client_id,
        period_start=period_start,
        period_end=period_end,
    )
