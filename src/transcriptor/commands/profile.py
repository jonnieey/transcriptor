import click

from transcriptor.base import Transcriptor
from transcriptor.view import ConsoleView

app = Transcriptor()


@click.group()
def cli(**kwargs):
    """Profile actions."""


@cli.command()
def show(**kwargs):
    """Show profile"""
    profile = app.profile
    if profile:
        cols, rows = (profile.cols(), profile.rows())
        ConsoleView().vertical_table(cols, rows)


@cli.command()
@click.option("-f", "--first_name", help="Specify first name")
@click.option("-l", "--last_name", help="Specify last name")
@click.option("-a", "--area", help="Specify area")
@click.option("-c", "--country", help="Specify country")
def edit(**kwargs):
    """Edit profile"""
    profile = app.get_profile()
    to_update_dict = {k: v for k, v in kwargs.items() if v is not None}
    profile.__dict__.update(to_update_dict)
    app.add_profile(profile)
