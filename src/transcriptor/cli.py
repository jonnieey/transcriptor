# type: ignore
import os
import sys
from argparse import Namespace
from copy import copy
from datetime import datetime
from pathlib import Path
from typing import Optional

import cmd2
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style

from transcriptor.base import Transcriptor
from transcriptor.utils import (
    date_validator,
    extract_date_due,
    extract_job_number,
    file_validator,
    get_media_duration,
    invoice_template_themes,
    job_type_validator,
    month_day_to_date,
    parse_conditions,
    parse_conditions_as_dict,
    positive_number_validator,
    template_validator,
    yes_no_validator,
)
from transcriptor.view import TranscriptorView

base_parser = cmd2.Cmd2ArgumentParser(description="Transcriptor CLI")
base_subparsers = base_parser.add_subparsers(
    title="subcommands", help="subcommand help"
)

show_parser = base_subparsers.add_parser("show", help="show object")
show_subparsers = show_parser.add_subparsers(
    title="subcommands", help="subcommand help"
)
show_config_parser = show_subparsers.add_parser("config", help="show config")
show_profile_parser = show_subparsers.add_parser(
    "profile", help="show profile"
)
show_clients_parser = show_subparsers.add_parser(
    "clients", help="show client"
)
show_rates_parser = show_subparsers.add_parser("rates", help="show rates")
show_jobs_parser = show_subparsers.add_parser("jobs", help="show jobs")
show_cutoffs_parser = show_subparsers.add_parser(
    "cutoffs", help="show cutoffs"
)
show_version_parser = show_subparsers.add_parser(
    "version", help="show version"
)

show_clients_parser.add_argument(
    "-w",
    "--where",
    action="append",
    help='Specify conditions in the format "field[operator]value", e.g., -w id<=1 -w amount>0',
)
show_clients_parser.add_argument(
    "-r",
    "--raw",
    help="Raw sql query",
)

show_rates_parser.add_argument(
    "-r",
    "--raw",
    help="Raw sql query",
)
show_rates_parser.add_argument(
    "-w",
    "--where",
    action="append",
    help='Specify conditions in the format "field[operator]value", e.g., -w id<=1 -w amount>0',
)

show_jobs_parser.add_argument(
    "-w",
    "--where",
    action="append",
    help='Specify conditions in the format "field[operator]value", e.g., -w id<=1 -w amount>0',
)
show_jobs_parser.add_argument(
    "-a",
    "--all",
    action="store_true",
    help="Show all jobs",
)
show_jobs_parser.add_argument(
    "-r",
    "--raw",
    help="Raw sql query",
)


add_parser = base_subparsers.add_parser("add", help="add object")
add_subparsers = add_parser.add_subparsers(
    title="subcommands", help="subcommand help"
)
add_client_parser = add_subparsers.add_parser("client", help="add client")

add_client_parser.add_argument(
    "-n",
    "--name",
    type=str,
    help="client name",
)
add_client_parser.add_argument(
    "-e",
    "--email",
    type=str,
    help="client email",
)

add_job_parser = add_subparsers.add_parser("job", help="add job")

add_job_parser.add_argument(
    "-f",
    "--file",
    type=str,
    help="Job File Path",
)
add_job_parser.add_argument("-c", "--client_id", type=int, help="Client ID")
add_job_parser.add_argument("-j", "--job_number", help="Job Number")
add_job_parser.add_argument("-r", "--date_received", help="Date Received")
add_job_parser.add_argument("-d", "--date_due", help="Date Due")
add_job_parser.add_argument("-q", "--quantity", help="Quantity")
add_job_parser.add_argument("-w", "--work_on_file", help="Work On File")
add_job_parser.add_argument("-t", "--job_type", help="Job Type")
add_job_parser.add_argument("-T", "--job_template", help="Job Template")
add_job_parser.add_argument("-N", "--note", help="Job Note")

add_cutoffs_parser = add_subparsers.add_parser(
    "cutoffs", help="generate cutoffs file from docx"
)
add_cutoffs_parser.add_argument(
    "-f",
    "--file",
    type=str,
    help="Cutoffs docx File Path",
)
add_cutoffs_parser.add_argument("-d", "--date_fmt", help="Date Format")
add_cutoffs_parser.add_argument("-y", "--year", help="Year for cutoffs")


update_parser = base_subparsers.add_parser("update", help="update object")
update_subparsers = update_parser.add_subparsers(
    title="subcommands", help="subcommand help"
)
update_config_parser = update_subparsers.add_parser(
    "config", help="update config"
)

update_config_parser.add_argument("-b", "--base-dir", help="base directory")
update_config_parser.add_argument("-d", "--date-format", help="date format")

update_profile_parser = update_subparsers.add_parser(
    "profile", help="update profile"
)
update_profile_parser.add_argument("-n", "--name", help="name")
update_profile_parser.add_argument("-a", "--area", help="area")

update_profile_parser.add_argument("-c", "--country", help="country")


update_client_parser = update_subparsers.add_parser(
    "client", help="update client"
)
update_client_parser.add_argument("-r", "--raw", help="Raw sql query")
update_client_parser.add_argument(
    "-w",
    "--where",
    action="append",
    help='Specify conditions in the format "field[operator]value", e.g., -w id<=1 -w amount>0',
)
update_client_parser.add_argument(
    "-v",
    "--values",
    action="append",
    help='Specify values in the format "field=value", e.g., -v id=1 -v amount=100',
)

update_rates_parser = update_subparsers.add_parser(
    "rates", help="update rates"
)
update_rates_parser.add_argument("-r", "--raw", help="Raw sql query")
update_rates_parser.add_argument(
    "-w",
    "--where",
    action="append",
    help='Specify conditions in the format "field[operator]value", e.g., -w id<=1 -w amount>0',
)
update_rates_parser.add_argument(
    "-v",
    "--values",
    action="append",
    help='Specify values in the format "field=value", e.g., -v id=1 -v amount=100',
)

update_jobs_parser = update_subparsers.add_parser("jobs", help="update job")
update_jobs_parser.add_argument("-r", "--raw", help="Raw sql query")
update_jobs_parser.add_argument(
    "-w",
    "--where",
    action="append",
    help='Specify conditions in the format "field[operator]value", e.g., -w id<=1 -w amount>0',
)
update_jobs_parser.add_argument(
    "-v",
    "--values",
    action="append",
    help='Specify values in the format "field=value", e.g., -v id=1 -v amount=100',
)

delete_parser = base_subparsers.add_parser("delete", help="delete object")
delete_subparsers = delete_parser.add_subparsers(
    title="subcommands", help="subcommand help"
)
delete_client_parser = delete_subparsers.add_parser(
    "clients", help="delete client"
)

delete_client_parser.add_argument(
    "-r",
    "--raw",
    help="Raw sql query",
)

delete_client_parser.add_argument(
    "-w",
    "--where",
    action="append",
    help='Specify conditions in the format "field[operator]value", e.g., -w id<=1',
)
delete_client_parser.add_argument(
    "-P", "--purge", action="store_true", help="Purge client data"
)
delete_client_parser.add_argument(
    "-N",
    "--no-confirm",
    action="store_true",
    help="Delete without confirmation",
)

delete_jobs_parser = delete_subparsers.add_parser("jobs", help="delete job")
delete_jobs_parser.add_argument(
    "-r",
    "--raw",
    help="Raw sql query",
)

delete_jobs_parser.add_argument(
    "-w",
    "--where",
    action="append",
    help='Specify conditions in the format "field[operator]value", e.g., -w id<=1',
)
delete_jobs_parser.add_argument(
    "-P", "--purge", action="store_true", help="Purge job data"
)
delete_jobs_parser.add_argument(
    "-N",
    "--no-confirm",
    action="store_true",
    help="Delete without confirmation",
)

invoice_parser = base_subparsers.add_parser(
    "invoice", help="generate invoice"
)
invoice_parser.add_argument("-c", "--client_id", help="Client ID")
invoice_parser.add_argument(
    "-w",
    "--where",
    action="append",
    help='Specify conditions in the format "field[operator]value", e.g., -w id<=1 -w amount>0',
)
invoice_parser.add_argument("-r", "--raw", help="Raw sql query")
invoice_parser.add_argument(
    "-p", "--print", action="store_true", help="Print invoice"
)
invoice_parser.add_argument(
    "-T", "--table", action="store_true", help="Print cutoffs table"
)
invoice_parser.add_argument(
    "-S",
    "--summary",
    action="store_true",
    help="Print annual summary invoice",
)
invoice_parser.add_argument(
    "-l", "--previous_year_cutoff", help="Previous year last cutoff"
)
invoice_parser.add_argument(
    "-t",
    "--invoice_template",
    help="Select invoice template",
    default="default",
    choices=invoice_template_themes(),
)

purge_parser = base_subparsers.add_parser(
    "purge", help="purge job media files, ex. m4a, mp3, mp4"
)
purge_parser.add_argument(
    "-w",
    "--where",
    action="append",
    help='Specify conditions in the format "field[operator]value", e.g., -w id<=1 -w amount>0',
)
purge_parser.add_argument("-r", "--raw", help="Raw sql query")


class TranscriptorCMD(cmd2.Cmd):
    prompt = "(trans5) "

    def __init__(self, app: None = None, history=True, alias=True):
        self.app = app or Transcriptor()
        history_file = (
            self.app.base_dir.joinpath(".history") if history else None
        )
        alias_script = (
            self.app.CONFIG_DIR.joinpath(".cmd2rc") if alias else None
        )
        super().__init__(
            persistent_history_file=history_file,
            persistent_history_length=500,
            allow_cli_args=False,
            startup_script=alias_script,
        )
        self.debug = True
        self.add_settable(cmd2.Settable("debug", bool, "debug", self))
        style = Style.from_dict(
            {
                "prompt": "bg:#000000 #00aa00 bold",  # black background, green text, bold text.
            }
        )
        self.session = PromptSession(style=style)

    def do_EOF(self, arg):
        """
        Exit
        """
        self.poutput("\n** Exiting program, bye **")
        return True

    def do_exit(self, arg):
        """Exit"""
        self.poutput("\n** Exiting program, bye **")
        return True

    def do_quit(self, arg: str):
        """Exit"""
        self.poutput("\n** Exiting program, bye **")
        return True

    def emptyline(self):
        pass

    def do_clear(self, arg):
        """Clear screen"""
        os.system("clear")

    def show_config(self, arg: Namespace):
        """
        Show configuration
        Ex.
           show config
        """
        config = self.app.config
        TranscriptorView().print_table(config.__dict__)

    show_config_parser.set_defaults(func=show_config)

    def show_profile(self, arg: Namespace):
        """
        Show profile
        Ex.
           show profile
        """
        if profile := self.app.profile:
            TranscriptorView().print_table(profile.__dict__)

    show_profile_parser.set_defaults(func=show_profile)

    def show_clients(self, args: Optional[Namespace]):
        """
        Show clients
        Ex.
           show clients
        """
        if args:
            if args.raw:
                clients = self.app.api.get_clients(raw_sql_stmt=args.raw)
            elif args.where:
                conditions = parse_conditions(args.where)
                clients = self.app.api.get_clients(conditions=conditions)
            else:
                clients = self.app.api.get_clients()
        else:
            clients = self.app.api.get_clients()
        TranscriptorView().print_table(clients, orientation="horizontal")

    show_clients_parser.set_defaults(func=show_clients)

    def show_rates(self, args: Namespace):
        if args.raw:
            rates = self.app.api.get_rates(raw_sql_stmt=args.raw)
        elif args.where:
            conditions = parse_conditions(args.where)
            rates = self.app.api.get_rates(conditions=conditions)
        else:
            rates = self.app.api.get_rates()
        TranscriptorView().print_table(rates, orientation="horizontal")

    show_rates_parser.set_defaults(func=show_rates)

    def show_jobs(self, args: Namespace):
        if args:
            if args.raw:
                jobs = self.app.api.get_jobs(raw_sql_stmt=args.raw)
            elif args.where:
                conditions = parse_conditions(args.where)
                jobs = self.app.api.get_jobs(conditions=conditions)
            elif args.all:
                jobs = self.app.api.get_jobs()
            else:
                jobs = self.app.api.get_jobs(
                    conditions={"status": [("=", "Pending")]}
                )

        TranscriptorView().print_table(jobs, orientation="horizontal")

    show_jobs_parser.set_defaults(func=show_jobs)

    def show_cutoffs(self, args: Namespace):
        cutoffs = self.app.load_cutoffs(as_str=True)
        TranscriptorView().print_table(cutoffs, orientation="vertical")

    show_cutoffs_parser.set_defaults(func=show_cutoffs)

    def show_version(self, args: Namespace):
        self.poutput(f"Version: {self.app.version}")

    show_version_parser.set_defaults(func=show_version)

    @cmd2.with_argparser(show_parser)
    def do_show(self, args: Namespace):
        """
        Show command help
        """
        func = getattr(args, "func", None)
        if func is not None:
            func(self, args)
        else:
            self.do_help("base")

    def add_client(self, args: Namespace):
        if args.name and args.email:
            self.app.create_client(name=args.name, email=args.email)
        else:
            self.poutput("Name and email are required.")

    add_client_parser.set_defaults(func=add_client)

    def add_job(self, args: Namespace):
        if args.file:
            if not Path(args.file).exists():
                self.poutput(f"File not found: {args.file}")
                return
        else:
            args.file = self.session.prompt(
                "Enter job file path: ", validator=file_validator
            )

        def job_callback(job_file):
            tmp_args = copy(args)

            client_id = tmp_args.client_id
            job_number = tmp_args.job_number
            date_received = tmp_args.date_received
            date_due = tmp_args.date_due
            date_format = self.app.config.date_format

            if not client_id:
                self.show_clients(args=None)
                client_id = int(
                    self.session.prompt(
                        "Enter client id: ",
                        validator=positive_number_validator,
                    )
                )
                tmp_args.client_id = client_id  # Update the original args

            if not job_number:
                job_number = extract_job_number(
                    str(job_file)
                ) or self.session.prompt("Enter job number: ")
                tmp_args.job_number = job_number  # Update the original args

            if not date_received:
                date_received = self.session.prompt(
                    f"Enter date received [{date_format}]: ",
                    default=str(datetime.now().strftime(date_format)),
                    validator=date_validator,
                )
                tmp_args.date_received = (
                    date_received  # Update the original args
                )
            if not date_due:
                date_due = self.session.prompt(
                    f"Enter date due [{date_format}]: ",
                    default=month_day_to_date(extract_date_due(args.file)),
                    validator=date_validator,
                )
                tmp_args.date_due = date_due  # Update the original args

            return {
                "client_id": client_id,
                "job_number": job_number,
                "date_received": date_received,
                "date_due": date_due,
            }

        def task_callback(task_file):
            tmp_args = copy(args)

            work_on_file = tmp_args.work_on_file
            job_type = tmp_args.job_type
            total_quantity = None
            quantity = tmp_args.quantity
            job_template = tmp_args.job_template
            note = tmp_args.note

            if not work_on_file:
                work_on_file = self.session.prompt(
                    f"Enter work on file: ...{'/'.join(task_file.parts[-2:])}:",
                    validator=yes_no_validator,
                )
                tmp_args.work_on_file = work_on_file
            if not tmp_args.work_on_file.strip().lower().startswith("y"):
                return

            if not job_type:
                job_type = self.session.prompt(
                    "Enter job type: ", validator=job_type_validator
                )
                tmp_args.job_type = job_type
            total_quantity = get_media_duration(task_file)
            if not quantity:
                quantity = self.session.prompt(
                    "Enter quantity: ", default=str(total_quantity)
                )
                tmp_args.quantity = quantity

            if not job_template:
                job_template = self.session.prompt(
                    "Enter job template: ", validator=template_validator
                )
                tmp_args.job_template = job_template
            if not note:
                note = self.session.prompt("Enter notes: ", default="")
                tmp_args.notes = note

            return {
                "work_on_file": work_on_file,
                "job_type": job_type.lower(),
                "total_quantity": total_quantity,
                "quantity": quantity,
                "job_template": job_template,
                "note": note,
            }

        self.app.create_job(
            job_file=args.file,
            job_callback=job_callback,
            task_callback=task_callback,
        )

    add_job_parser.set_defaults(func=add_job)

    def add_cutoffs(self, args: Namespace):
        if args.file:
            if not Path(args.file).exists():
                self.poutput(f"File not found: {args.file}")
                return
        else:
            args.file = self.session.prompt(
                "Enter cutoff file path: ", validator=file_validator
            )

        cutoffs = self.app.generate_cutoff_list_from_docx(
            docx_path=args.file, date_fmt=args.date_fmt
        )
        self.app.save_cutoffs(cutoffs, year=args.year)

    add_cutoffs_parser.set_defaults(func=add_cutoffs)

    @cmd2.with_argparser(add_parser)
    def do_add(self, args: Namespace):
        """
        Add command help
        """
        func = getattr(args, "func", None)
        if func is not None:
            func(self, args)
        else:
            self.do_help("base")

    def update_config(self, args: Namespace):
        config = self.app.config
        if args.base_dir:
            config.base_dir = args.base_dir
        if args.date_format:
            config.date_format = args.date_format
        self.app.config = config
        self.app.save_config()

    update_config_parser.set_defaults(func=update_config)

    def update_profile(self, args: Namespace):
        profile = self.app.profile
        if args.name:
            profile.name = args.name
        if args.area:
            profile.area = args.area
        if args.country:
            profile.country = args.country
        self.app.profile = profile
        self.app.save_profile()

    update_profile_parser.set_defaults(func=update_profile)

    def update_clients(self, args: Namespace):
        if args.raw:
            self.app.api.update("clients", raw_sql_stmt=args.raw)
        if args.where and args.values:
            where = parse_conditions(args.where)
            values = parse_conditions_as_dict(args.values)
            self.app.api.update_clients(conditions=where, values=values)
        else:
            self.poutput("Please provide conditions and values")
            return

    update_client_parser.set_defaults(func=update_clients)

    def update_rates(self, args: Namespace):
        if args.raw:
            self.app.api.update_rates(raw_sql_stmt=args.raw)
            return
        if args.where and args.values:
            where = parse_conditions(args.where)
            values = parse_conditions_as_dict(args.values)
            self.app.api.update_rates(conditions=where, values=values)
            return
        else:
            self.poutput("Please provide conditions and values")
            return

    update_rates_parser.set_defaults(func=update_rates)

    def update_job(self, args: Namespace):
        if args.raw:
            self.app.update_jobs(raw_sql_stmt=args.raw)
        elif args.where and args.values:
            where = parse_conditions(args.where)
            values = parse_conditions_as_dict(args.values)
            self.app.update_jobs(conditions=where, values=values)
        else:
            self.poutput("Please provide conditions and values")
            return

    update_jobs_parser.set_defaults(func=update_job)

    @cmd2.with_argparser(update_parser)
    def do_update(self, args: Namespace):
        """
        Update command help
        """
        func = getattr(args, "func", None)
        if func is not None:
            func(self, args)
        else:
            self.do_help("base")

    def delete_clients(self, args: Namespace):
        clients = None

        if not args.where and not args.raw:
            self.poutput("Please provide conditions to delete")
            return

        if args.raw:
            clients = self.app.api.get_clients(raw_sql_stmt=args.raw)

        elif args.where:
            conditions = parse_conditions(args.where)
            clients = self.app.api.get_clients(conditions=conditions)

        if not clients:
            self.poutput("No clients found")
            return

        if args.no_confirm:
            if args.purge:
                self.poutput(
                    "\n** DELETING CLIENTS WILL DELETE ALL CLIENT DATA (NO CONFIRMATION)**\n"
                )
            to_delete = self.session.prompt(
                "Are you sure you want to delete clients (NO CONFIRM)  (y/n): ",
                validator=yes_no_validator,
            )
            if to_delete.lower().startswith("y"):
                self.app.delete_clients(
                    conditions=conditions,
                    raw_sql_stmt=args.raw,
                    purge=args.purge,
                )
        else:
            for client in clients:
                client_name = client["name"]
                to_delete = self.session.prompt(
                    f"Are you sure you want to delete {client_name}? (y/n): ",
                    validator=yes_no_validator,
                )

                if to_delete.lower().startswith("y"):
                    self.poutput(
                        "\n** DELETING CLIENT WILL DELETE CLIENT'S JOBS AND RATES **\n"
                    )
                    if args.purge:
                        self.poutput(
                            "\n** DELETING CLIENT WILL DELETE ALL CLIENT DATA**\n"
                        )
                    confirm_delete = self.session.prompt(
                        f"TYPE {client_name} to confirm: "
                    )

                    if confirm_delete == client_name:
                        self.app.delete_clients(
                            conditions={"name": [("=", client_name)]},
                            purge=args.purge,
                        )
                    else:
                        self.poutput("Operation aborted")
                        return

    delete_client_parser.set_defaults(func=delete_clients)

    def delete_jobs(self, args):
        jobs = None
        if args.raw:
            jobs = self.app.api.get_jobs(raw_sql_stmt=args.raw)
        if not args.where:
            self.poutput("Please provide conditions to delete")
            return
        else:
            conditions = parse_conditions(args.where)
            jobs = self.app.api.get_jobs(conditions=conditions)

        if not jobs:
            self.poutput("No jobs found")
            return

        if args.no_confirm:
            if args.purge:
                self.poutput(
                    "\n** DELETING CLIENTS WILL DELETE ALL CLIENT DATA (NO CONFIRMATION)**\n"
                )
            confirm_delete = self.session.prompt(
                f"Are you sure you want to delete jobs (NO CONFIRMATION)? (y/n): ",
                validator=yes_no_validator,
            )
            if confirm_delete.lower().startswith("y"):
                self.app.delete_jobs(
                    conditions=conditions,
                    raw_sql_stmt=args.raw,
                    purge=args.purge,
                )
        else:
            for job in jobs:
                confirm_delete = self.session.prompt(
                    f"""Are you sure you want to delete {job['job_number']}? (y/n):
                    """,
                    validator=yes_no_validator,
                )

                if confirm_delete.lower().startswith("y"):
                    self.app.delete_jobs(
                        conditions=conditions,
                        raw_sql_stmt=args.raw,
                        purge=args.purge,
                    )
                else:
                    self.poutput("Operation aborted")
                    return

    delete_jobs_parser.set_defaults(func=delete_jobs)

    @cmd2.with_argparser(delete_parser)
    def do_delete(self, args: Namespace):
        """
        Delete command help
        """
        func = getattr(args, "func", None)
        if func is not None:
            func(self, args)
        else:
            self.do_help("base")

    def invoice(self, args: Namespace):
        if not any([args.raw, args.table, args.where, args.summary]):
            error = """Conditions must be provided or summary flag must be set.
    Ex. invoice -w 'date_submitted > \"2025-01-01\" -w date_submitted <= \"2025-01-31\"
            """
            self.poutput(error)
            self.do_help("invoice")
            return
        if not args.client_id:
            self.show_clients(args=None)
            client_id = int(
                self.session.prompt(
                    "Enter client id: ", validator=positive_number_validator
                )
            )
            args.client_id = client_id  # Update the original args
        if args.summary:
            html, client_name = self.app.generate_summary_invoice(
                client_id=args.client_id,
                previous_year_cutoff=args.previous_year_cutoff,
            )
        if args.table:
            cutoffs = self.app.load_cutoffs(as_str=True)
            cutoffs = [
                ["index" if row == 0 else str(idx)] + row
                for idx, row in enumerate(cutoffs)
            ]
            TranscriptorView().print_table(cutoffs)
            cutoff_idx = self.session.prompt(
                "select deposit date. Use index number: ",
                validator=positive_number_validator,
            )
            previous_cutoff, cutoff = self.app.select_cutoff_period(
                int(cutoff_idx)
            )
            raw_cutoff_condition = f""" date_submitted > '{previous_cutoff}'
                  AND date_submitted <= '{cutoff}'
                  """
            cutoff_condition = [
                f"date_submitted>{previous_cutoff}",
                f"date_submitted<={cutoff}",
            ]

        if args.raw:
            if args.table:
                args.raw = args.raw + f" AND {raw_cutoff_condition}"
            html, client_name = self.app.generate_invoice(
                client_id=args.client_id,
                raw_sql_stmt=args.raw,
                invoice_theme=args.invoice_template,
            )
        elif args.where:
            if args.table:
                args.where = args.where + cutoff_condition
            conditions = parse_conditions(args.where)
            html, client_name = self.app.generate_invoice(
                client_id=args.client_id,
                conditions=conditions,
                invoice_theme=args.invoice_template,
            )
        else:
            if args.table:
                conditions = parse_conditions(cutoff_condition)
                html, client_name = self.app.generate_invoice(
                    client_id=args.client_id,
                    conditions=conditions,
                    invoice_theme=args.invoice_template,
                )
        if args.print:
            self.app.html_to_pdf(
                html, client_name, summary_invoice=args.summary
            )
        else:
            md = self.app.to_md(html)
            TranscriptorView().console.print(md)

    invoice_parser.set_defaults(func=invoice)

    @cmd2.with_argparser(invoice_parser)
    def do_invoice(self, args: Namespace):
        """
        Delete command help
        """
        func = getattr(args, "func", None)
        if func is not None:
            func(self, args)
        else:
            self.do_help("base")

    def purge(self, args):
        if not any([args.raw, args.where]):
            self.poutput("Please provide conditions to purge")
            return
        if args.raw:
            jobs = self.app.api.get_jobs(raw_sql_stmt=args.raw)
        else:
            conditions = parse_conditions(args.where)
            jobs = self.app.api.get_jobs(conditions=conditions)
        if not jobs:
            self.poutput("No jobs found")
        else:
            confirm_delete = self.session.prompt(
                "Are you sure you want to delete (y/n) :",
                validator=yes_no_validator,
            )
            if confirm_delete.lower().startswith("y"):
                self.app.purge_job_files(jobs)

    purge_parser.set_defaults(func=purge)

    @cmd2.with_argparser(purge_parser)
    def do_purge(self, args: Namespace):
        """
        Delete command help
        """
        func = getattr(args, "func", None)
        if func is not None:
            func(self, args)
        else:
            self.do_help("base")


def main():
    c = TranscriptorCMD()
    try:
        sys.exit(c.cmdloop())
    except (KeyboardInterrupt, EOFError):
        c.poutput("\n** Exiting program, bye **\n")
        return True


if __name__ == "__main__":
    main()
