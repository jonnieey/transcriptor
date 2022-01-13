import click

from transcriptor.api import add_client, list_clients


@click.group()
def cli(**kwargs):
    "Clients actions"
    pass


@cli.command()
@click.option("-n", "--name", help="Specify new client's name")
@click.option("-e", "--email", help="Specify new client's email")
def add(name, email):
    """Add client"""
    if name is None and email is None:
        name = click.prompt("Enter clients name")
        email = click.prompt("Enter clients Email")
    add_client(name, email)


@cli.command()
def list():
    """List clients"""
    list_clients()
