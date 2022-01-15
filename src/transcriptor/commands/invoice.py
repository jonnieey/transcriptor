import click

from transcriptor.api import create_invoice


@click.group()
def cli(**kwargs):
    "Invoice actions"
    pass


@cli.command()
@click.option("-c", "--client", required=True, help="Specify client", prompt=True)
def create(client=None, **kwargs):
    """Create client invoice"""
    create_invoice(client)
