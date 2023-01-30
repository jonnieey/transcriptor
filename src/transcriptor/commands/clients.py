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
@click.option("-n", "--name", prompt="Enter client name", help="Client name")
@click.option("-e", "--email", prompt="Enter client email", help="Client email")
def create(name, email, **kwargs):
    """Create new client"""
    try:
        app.add_client(name=name, email=email)
    except Exception as error:
        logger.error(error)


@cli.command()
def list(**kwargs):
    """List all clients"""
    cols = ["id", "name", "email", "normal", "expedite", "interpreted"]
    scalars = app.api.list_clients()
    if scalars:
        ConsoleView().vertical_table(cols, scalars, headers=cols)


@cli.command()
@click.argument("client_name")
@click.option("-n", "--new-name", help="New client name")
@click.option("-e", "--new-email", help="New client email")
@click.option("-r", "--new-rates", type=(float, float, float), help="New client rates")
def edit(client_name, new_name, new_email, new_rates, **kwargs):
    """Edit client attributes"""

    app.api.edit_client(
        client_name=client_name,
        new_name=new_name,
        new_email=new_email,
        new_rates=new_rates,
    )


@cli.command()
@click.argument("client_name")
def delete(client_name, **kwargs):
    """Delete client from database"""
    app.api.delete_client(client_name=client_name)
