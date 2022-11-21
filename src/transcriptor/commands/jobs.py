import click
from sqlalchemy import select

from transcriptor.base import Transcriptor
from transcriptor.models import JobModel
from transcriptor.view import ConsoleView

app = Transcriptor()


@click.group()
def cli(**kwargs):
    """Job actions."""
    pass


@cli.command()
def list(**kwargs):
    jobs = app.api.execute_sql("SELECT * FROM Jobs").fetchall()
    if jobs:
        cols = tuple(jobs[0]._asdict().keys())
        rows = jobs
        ConsoleView().vertical_table(cols, rows, headers=cols)


@cli.command()
@click.argument("id")
def delete(id, **kwargs):
    with app.api.session as session:
        j = session.execute(select(JobModel).filter_by(id=f"{id}")).scalar_one()
        session.delete(j)
        session.commit()
