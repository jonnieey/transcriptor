import click
import logging
from sqlalchemy import select

from transcriptor.base import Transcriptor
from transcriptor.models import ClientModel
from transcriptor.view import ConsoleView

logger = logging.getLogger(__name__)

app = Transcriptor()


@click.group()
def cli(**kwargs):
    """Clients actions."""
    pass


@cli.command()
def list(**kwargs):
    clients = app.api.execute_sql("SELECT * FROM Clients").fetchall()
    if clients:
        cols = clients[0]._asdict().keys()
        rows = clients
        ConsoleView().vertical_table(cols, rows, headers=cols)


@cli.command()
@click.option("-n", "--name", prompt="Enter client name", help="Client name")
@click.option("-e", "--email", prompt="Enter client email", help="Client email")
def create(name, email, **kwargs):
    """Create new client"""
    try:
        client = app.api.create_client(name, email)
        app.api.save_client(client)
    except Exception as error:
        logger.error(error)


@cli.command()
@click.argument("client")
@click.option("-n", "--name", help="New client name")
@click.option("-e", "--email", help="New client email")
def edit(client, name, email, **kwargs):
    with app.api.session as session:
        c = session.execute(
            select(ClientModel).filter_by(name=f"{client}")
        ).scalar_one()
        if name:
            c.name = name
        if email:
            c.email = email
        session.commit()


@cli.command()
@click.argument("client")
def delete(client, **kwargs):
    with app.api.session as session:
        c = session.execute(
            select(ClientModel).filter_by(name=f"{client}")
        ).scalar_one()
        session.delete(c)
        session.commit()
