import re

import click

from transcriptor.api import add_client, list_clients


def validate_email(ctx, params, value):
    match = re.match(r"^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$", value)
    if match is None:
        raise click.BadParameter("Enter a valid email address")
    else:
        return value.lower()


@click.group()
def cli(**kwargs):
    "Clients actions"
    pass


@cli.command()
@click.option("-n", "--name", required=True, prompt=True, help="Specify new client's name")
@click.option("-e", "--email", required=True, prompt=True, help="Specify new client's email", callback=validate_email)
def add(name, email, **kwargs):
    """Add client"""
    add_client(name, email)


@cli.command()
def list():
    """List clients"""
    list_clients()
