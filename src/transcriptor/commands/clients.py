import logging

import click

from transcriptor.base import Transcriptor
from transcriptor.view import ConsoleView

logger = logging.getLogger(__name__)

app = Transcriptor()


@click.group()
def cli(**kwargs):
    """Clients actions."""
    pass


@cli.command()
def list(**kwargs):
    cols, rows = app.api.list_clients()
    if all([cols, rows]):
        ConsoleView().vertical_table(cols, rows, headers=cols)


@cli.command()
@click.option("-n", "--name", prompt="Enter client name", help="Client name")
@click.option("-e", "--email", prompt="Enter client email", help="Client email")
def create(name, email, **kwargs):
    """Create new client"""
    try:
        client = app.api.create_client(name=name, email=email)
        app.api.save_client(client)
    except Exception as error:
        logger.error(error)


@cli.command()
@click.argument("client_name")
@click.option("-n", "--new-name", help="New client name")
@click.option("-e", "--new-email", help="New client email")
@click.option("-r", "--new-rates", type=(float, float, float), help="New client rates")
def edit(client_name, new_name, new_email, new_rates, **kwargs):
    app.api.edit_client(
        client_name=client_name,
        new_name=new_name,
        new_email=new_email,
        new_rates=new_rates,
    )


@cli.command()
@click.argument("client_name")
def delete(client_name, **kwargs):
    app.api.delete_client(client_name=client_name)
