import sys
from copy import copy
from datetime import date

import click

from transcriptor.api import (
    create_job,
    get_client_object,
    list_all_jobs,
    list_client_jobs,
)
from transcriptor.methods import DATE_FMT, get_date_due, get_date_received, update_job

TODAY = date.today().strftime(DATE_FMT)


def check_client(ctx, params, value):
    if get_client_object(value) is None:
        raise click.UsageError("Client %s does not exist" % (value))
        sys.exit("Client %s does not exist" % (value))
    else:
        return value


@click.group()
def cli(**kwargs):
    "Job actions"
    pass


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "-c",
    "--client",
    prompt="Enter client's name",
    callback=check_client,
    help="Specify client name",
)
@click.option(
    "-r",
    "--date-received",
    default=TODAY,
    required=True,
    prompt="Enter date job received",
    help="Specify date job received fmt: YYYY-MM-DD",
)
@click.option(
    "-d",
    "--date-due",
    required=True,
    prompt="Enter date job due",
    help="Specify date job due fmt: YYYY-MM-DD",
)
@click.option(
    "-n",
    "--note",
    prompt="Enter notes on job",
    default="",
    help="Notes on job",
)
def create(file, date_received=None, date_due=None, client=None, note=None, **kwargs):
    """Create job"""
    date_received = get_date_received(date_received)
    date_due = get_date_due(date_due)

    client_obj = get_client_object(client)
    create_job(file, date_received, date_due, client_obj, note)


@cli.command()
@click.option("-c", "--client", help="Specify client")
@click.option("-a", "--all", is_flag=True, help="Specify client")
@click.option("-s", "--per-client", is_flag=True, help="List job per client")
@click.option("-p", "--show-path", is_flag=True, help="List job per client")
def list(client=None, all=None, per_client=None, show_path=None, **kwargs):
    """List client's jobs"""
    if all is True:
        list_all_jobs(per_client=per_client, show_path=show_path)
        return

    if client is not None:
        list_client_jobs(client, show_path=show_path)
    else:
        client = click.prompt("Enter client's name")
        list_client_jobs(client, show_path=show_path)


def check_date_received(ctx, params, value):
    if value == None:
        return value

    if value == "":
        raise click.BadParameter("Enter valid argument [YYYY-MM-DD, or int]")

    d = get_date_received(value)
    if d is None:
        raise click.BadParameter("Enter valid argument [YYYY-MM-DD, or int]")
    else:
        return str(d)


def check_date_due(ctx, params, value):
    if value == None:
        return value

    if value == "":
        raise click.BadParameter("Enter valid argument [YYYY-MM-DD, or int]")

    d = get_date_due(value)
    if d is None:
        raise click.BadParameter("Enter valid argument [YYYY-MM-DD, or int]")
    else:
        return str(d)


@cli.command()
@click.argument("job_number", required=True, nargs=-1)
@click.option("-c", "--client", help="Specify client")
@click.option(
    "-r",
    "--date-received",
    help="Specify date job received fmt: YYYY-MM-DD",
    callback=check_date_received,
)
@click.option(
    "-d",
    "--date-due",
    help="Specify date job due fmt: YYYY-MM-DD",
    callback=check_date_due,
)
@click.option(
    "-b",
    "--date-submitted",
    help="Specify date job submitted fmt: YYYY-MM-DD",
    callback=check_date_received,
)
@click.option(
    "-s",
    "--status",
    type=click.Choice(["Pending", "Done"]),
    help="Specify status of job",
)
@click.option("-a", "--amount_paid", type=float, help="Specify amount paid")
@click.option("-q", "--quantity", type=float, help="Specify quantity")
def update(**kwargs):
    """Update job"""
    multiple = copy(kwargs)
    u = [
        kwargs["client"],
        kwargs["date_received"],
        kwargs["date_due"],
        kwargs["date_submitted"],
        kwargs["quantity"],
    ]
    if len(kwargs["job_number"]) > 1:
        if any(u):
            raise click.BadParameter(
                "Invalid options, use status or amount paid for multiple updates"
            )
        else:
            for j in kwargs["job_number"]:
                d = {k: v for k, v in kwargs.items() if v is not None}
                d.pop("job_number")
                d["job_number"] = j
                update_job(j, d)
