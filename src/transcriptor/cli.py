from transcriptor.base import Transcriptor
import os
import sys
import cmd2
from copy import copy
from pathlib import Path
from datetime import datetime
from transcriptor.view import TranscriptorView
from transcriptor.utils import (
    parse_conditions,
    parse_conditions_as_dict,
    extract_job_number,
    get_media_duration,
    file_validator,
    positive_number_validator,
    date_validator,
    yes_no_validator,
    job_type_validator,
    template_validator,
)
from prompt_toolkit import prompt

base_parser = cmd2.Cmd2ArgumentParser(description="Transcriptor CLI")
base_subparsers = base_parser.add_subparsers(
    title="subcommands", help="subcommand help"
)

show_parser = base_subparsers.add_parser("show", help="show object")
show_subparsers = show_parser.add_subparsers(
    title="subcommands", help="subcommand help"
)
show_config_parser = show_subparsers.add_parser("config", help="show config")
show_profile_parser = show_subparsers.add_parser("profile", help="show profile")
show_clients_parser = show_subparsers.add_parser("clients", help="show client")
show_rates_parser = show_subparsers.add_parser("rates", help="show rates")
show_jobs_parser = show_subparsers.add_parser("jobs", help="show jobs")
show_cutoffs_parser = show_subparsers.add_parser("cutoffs", help="show cutoffs")


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
add_subparsers = add_parser.add_subparsers(title="subcommands", help="subcommand help")
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


update_parser = base_subparsers.add_parser("update", help="update object")
update_subparsers = update_parser.add_subparsers(
    title="subcommands", help="subcommand help"
)
update_config_parser = update_subparsers.add_parser("config", help="update config")

update_config_parser.add_argument("-b", "--base-dir", help="base directory")
update_config_parser.add_argument("-d", "--date-format", help="date format")

update_profile_parser = update_subparsers.add_parser("profile", help="update profile")
update_profile_parser.add_argument("-f", "--first_name", help="first name")
update_profile_parser.add_argument("-l", "--last_name", help="last name")
update_profile_parser.add_argument("-a", "--area", help="area")

update_profile_parser.add_argument("-c", "--country", help="country")


update_client_parser = update_subparsers.add_parser("client", help="update client")
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

update_rates_parser = update_subparsers.add_parser("rates", help="update rates")
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
delete_client_parser = delete_subparsers.add_parser("clients", help="delete client")

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

invoice_parser = base_subparsers.add_parser("invoice", help="generate invoice")
invoice_parser.add_argument("-c", "--client_id", help="Client ID")
invoice_parser.add_argument(
    "-w",
    "--where",
    action="append",
    help='Specify conditions in the format "field[operator]value", e.g., -w id<=1 -w amount>0',
)
invoice_parser.add_argument("-r", "--raw", help="Raw sql query")
invoice_parser.add_argument("-p", "--print", action="store_true", help="Print invoice")
invoice_parser.add_argument(
    "-T", "--table", action="store_true", help="Print cutoffs table"
)


class TranscriptorCMD(cmd2.Cmd):
    prompt = "(trans5) "

    def __init__(self, app=None):
        self.app = app if app is not None else Transcriptor()
        history_file = self.app.base_dir.joinpath(".history")
        alias_script = self.app.CONFIG_DIR.joinpath(".cmd2rc")
        super().__init__(
            persistent_history_file=history_file,
            persistent_history_length=500,
            allow_cli_args=False,
            startup_script=alias_script,
        )
        self.debug = True
        self.add_settable(cmd2.Settable("debug", bool, "debug", self))

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

    def do_quit(self, arg):
        """Exit"""
        self.poutput("\n** Exiting program, bye **")
        return True

    def emptyline(self):
        pass

    def do_clear(self, arg):
        """Clear screen"""
        os.system("clear")

    def show_config(self, arg):
        """
        Show configuration
        Ex.
           show config
        """
        config = self.app.config
        TranscriptorView().print_table(config.__dict__)

    show_config_parser.set_defaults(func=show_config)

    def show_profile(self, arg):
        """
        Show profile
        Ex.
           show profile
        """
        if profile := self.app.profile:
            TranscriptorView().print_table(profile.__dict__)

    show_profile_parser.set_defaults(func=show_profile)

    def show_clients(self, args):
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

    def show_rates(self, args):
        rates = self.app.api.get_rates()
        TranscriptorView().print_table(rates, orientation="horizontal")

    show_rates_parser.set_defaults(func=show_rates)

    def show_jobs(self, args):
        if args:
            if args.raw:
                jobs = self.app.api.get_jobs(raw_sql_stmt=args.raw)
            elif args.where:
                conditions = parse_conditions(args.where)
                jobs = self.app.api.get_jobs(conditions=conditions)
            elif args.all:
                jobs = self.app.api.get_jobs()
            else:
                jobs = self.app.api.get_jobs(conditions={"status": [("=", "Pending")]})

        TranscriptorView().print_table(jobs, orientation="horizontal")

    show_jobs_parser.set_defaults(func=show_jobs)

    def show_cutoffs(self, args):
        cutoffs = self.app.load_cutoffs(as_str=True)
        TranscriptorView().print_table(cutoffs, orientation="vertical")

    show_cutoffs_parser.set_defaults(func=show_cutoffs)

    @cmd2.with_argparser(show_parser)
    def do_show(self, args):
        """
        Show command help
        """
        func = getattr(args, "func", None)
        if func is not None:
            func(self, args)
        else:
            self.do_help("base")

    def add_client(self, args):
        if args.name and args.email:
            self.app.create_client(name=args.name, email=args.email)
        else:
            self.poutput("Name and email are required.")

    add_client_parser.set_defaults(func=add_client)

    def add_job(self, args):
        if args.file:
            if not Path(args.file).exists():
                self.poutput(f"File not found: {args.file}")
                return
        else:
            args.file = prompt("Enter job file path: ", validator=file_validator)

        def job_callback(job_file):
            tmp_args = copy(args)

            client_id = tmp_args.client_id
            job_number = tmp_args.job_number
            date_received = tmp_args.date_received
            date_due = tmp_args.date_due

            if not client_id:
                self.show_clients(args=None)
                client_id = int(
                    prompt("Enter client id: ", validator=positive_number_validator)
                )
                tmp_args.client_id = client_id  # Update the original args

            if not job_number:
                job_number = extract_job_number(str(job_file)) or prompt(
                    "Enter job number: "
                )
                tmp_args.job_number = job_number  # Update the original args

            if not date_received:
                date_received = prompt(
                    f"Enter date received [{self.app.config.date_format}]: ",
                    default=str(datetime.now().strftime(self.app.config.date_format)),
                    validator=date_validator,
                )
                tmp_args.date_received = date_received  # Update the original args
            if not date_due:
                date_due = prompt(
                    f"Enter date due [{self.app.config.date_format}]: ",
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
                work_on_file = prompt(
                    f"Enter work on file: ...{'/'.join(task_file.parts[-2:])}: ",
                    validator=yes_no_validator,
                )
                tmp_args.work_on_file = work_on_file
            if not tmp_args.work_on_file.strip().lower().startswith("y"):
                return

            if not job_type:
                job_type = prompt("Enter job type: ", validator=job_type_validator)
                tmp_args.job_type = job_type
            total_quantity = get_media_duration(task_file)
            if not quantity:
                quantity = prompt("Enter quantity: ", default=str(total_quantity))
                tmp_args.quantity = quantity

            if not job_template:
                job_template = prompt(
                    "Enter job template: ", validator=template_validator
                )
                tmp_args.job_template = job_template
            if not note:
                note = prompt("Enter notes: ", default="")
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

    def add_cutoffs(self, args):
        if args.file:
            if not Path(args.file).exists():
                self.poutput(f"File not found: {args.file}")
                return
        else:
            args.file = prompt("Enter cutoff file path: ", validator=file_validator)

        if not args.date_fmt:
            cutoffs = self.app.generate_cutoff_list_from_docx(args.file, args.date_fmt)
        else:
            cutoffs = self.app.generate_cutoff_list_from_docx(args.file)
        self.app.save_cutoffs(cutoffs)

    add_cutoffs_parser.set_defaults(func=add_cutoffs)

    @cmd2.with_argparser(add_parser)
    def do_add(self, args):
        """
        Add command help
        """
        func = getattr(args, "func", None)
        if func is not None:
            func(self, args)
        else:
            self.do_help("base")

    def update_config(self, args):
        if args.base_dir:
            self.app.config.base_dir = args.base_dir
        if args.date_format:
            self.app.config.date_format = args.date_format
        self.app.save_config()

    update_config_parser.set_defaults(func=update_config)

    def update_profile(self, args):
        if args.first_name:
            self.app.profile.first_name = args.first_name
        if args.last_name:
            self.app.profile.last_name = args.last_name
        if args.area:
            self.app.profile.area = args.area
        if args.country:
            self.app.profile.contry = args.country
        self.app.save_profile()

    update_profile_parser.set_defaults(func=update_profile)

    def update_clients(self, args):
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

    def update_rates(self, args):
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

    def update_job(self, args):
        if args.raw:
            self.app.api.update_jobs(raw_sql_stmt=args.raw)
        if args.where and args.values:
            where = parse_conditions(args.where)
            values = parse_conditions_as_dict(args.values)
            self.app.api.update_jobs(conditions=where, values=values)
        else:
            self.poutput("Please provide conditions and values")
            return

    update_jobs_parser.set_defaults(func=update_job)

    @cmd2.with_argparser(update_parser)
    def do_update(self, args):
        """
        Update command help
        """
        func = getattr(args, "func", None)
        if func is not None:
            func(self, args)
        else:
            self.do_help("base")

    def delete_clients(self, args):
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

        for client in clients:
            to_delete = prompt(
                f"Are you sure you want to delete {client['name']}? (y/n): ",
                validator=yes_no_validator,
            )

            if to_delete.startswith("y") or to_delete.startswith("Y"):
                self.poutput(
                    "\n** DELETING CLIENT WILL DELETE CLIENT'S JOBS AND RATES **\n"
                )
                if args.purge:
                    self.poutput("\n** DELETING CLIENT WILL DELETE ALL CLIENT DATA**\n")
                confirm_delete = prompt(f"TYPE {client['name']} to confirm: ")

                if confirm_delete == client["name"]:
                    self.app.delete_clients(
                        conditions={"name": [("=", client["name"])]}, purge=args.purge
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

        for job in jobs:
            confirm_delete = prompt(
                f"Are you sure you want to delete {job['job_number']}? (y/n): ",
                validator=yes_no_validator,
            )

            if confirm_delete.startswith("y") or confirm_delete.startswith("Y"):
                self.app.delete_jobs(conditions=conditions, purge=args.purge)
            else:
                self.poutput("Operation aborted")
                return

    delete_jobs_parser.set_defaults(func=delete_jobs)

    @cmd2.with_argparser(delete_parser)
    def do_delete(self, args):
        """
        Delete command help
        """
        func = getattr(args, "func", None)
        if func is not None:
            func(self, args)
        else:
            self.do_help("base")

    def invoice(self, args):
        if not args.client_id:
            return
        if args.raw:
            html, client = self.app.generate_invoice(
                client_id=args.client_id, raw_sql_stmt=args.raw
            )
        elif args.where:
            conditions = parse_conditions(args.where)
            html, client = self.app.generate_invoice(
                client_id=args.client_id, conditions=conditions
            )
        if args.print:
            self.app.html_to_pdf(html, client)
        else:
            md = self.app.to_md(html)
            TranscriptorView().console.print(md)

    invoice_parser.set_defaults(func=invoice)

    @cmd2.with_argparser(invoice_parser)
    def do_invoice(self, args):
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
