import sys
from datetime import date

import click

from transcriptor.api import (
    create_job,
    get_client_object,
    list_all_jobs,
    list_client_jobs,
)
from transcriptor.methods import DATE_FMT, get_date_due, get_date_received, update_job
from transcriptor.utils import parse_job_due_date

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


def fetch_date_due() -> str:
    return parse_job_due_date(click.get_current_context().params["file"])


@cli.command()
@click.option(
    "-f", "--file", type=click.Path(exists=True), required=True, is_eager=True
)
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
    is_eager=True,
    default=fetch_date_due,
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
@click.option("-a", "--show_all", is_flag=True, help="Specify client")
@click.option("-s", "--per-client", is_flag=True, help="List job per client")
@click.option("-p", "--show-path", is_flag=True, help="Show job path")
@click.option(
    "-f",
    "--filter-by",
    type=click.Choice(["Pending", "Done", ""]),
    default="",
    help="Filter by word",
)
@click.option("-P", "--show-paid", is_flag=True, help="Include paid jobs")
def list(
    client=None,
    show_all=None,
    per_client=None,
    show_path=None,
    filter_by=None,
    show_paid=None,
    **kwargs
):
    """List client's jobs"""
    if show_all is True:
        list_all_jobs(
            per_client=per_client,
            show_path=show_path,
            filter_by=filter_by,
            show_paid=show_paid,
        )
        return

    if client is not None:
        list_client_jobs(
            client, show_path=show_path, filter_by=filter_by, show_paid=show_path
        )
    else:
        client = click.prompt("Enter client's name")
        list_client_jobs(
            client, show_path=show_path, filter_by=filter_by, show_paid=show_path
        )


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
@click.option(
    "-t",
    "--job-type",
    type=click.Choice(["Normal", "Interpreted", "Expedite"]),
    help="Specify job type",
)
def update(**kwargs):
    """Update job"""
    u = [
        kwargs["client"],
        kwargs["quantity"],
    ]
    if len(kwargs["job_number"]) > 1:
        if any(u):
            raise click.BadParameter(
                "Invalid options, use status or amount paid for multiple updates"
            )
    for j in kwargs["job_number"]:
        d = {k: v for k, v in kwargs.items() if v is not None}
        d.pop("job_number")
        d["job_number"] = j
        update_job(j, d)
