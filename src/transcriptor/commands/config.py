import logging

import click

from transcriptor.base import Transcriptor
from transcriptor.view import ConsoleView

logger = logging.getLogger(__name__)

app = Transcriptor()


@click.group()
def cli(**kwargs):
    """Configuration actions."""
    pass


@cli.command()
def show(**kwargs):
    """Show Configuration"""
    config = app.config
    cols, rows = (config.cols(), config.rows())
    ConsoleView().vertical_table(cols, rows)


@cli.command()
@click.option("-b", "--base-dir", help="Specify base directory")
@click.option("-d", "--date-format", help="Specify date format")
def edit(**kwargs):
    config = app.get_config()
    to_update_dict = {k: v for k, v in kwargs.items() if v is not None}
    config.__dict__.update(to_update_dict)
    app.add_config(config)
