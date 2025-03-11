from transcriptor.base import Transcriptor
import os
import sys
import cmd2
from copy import copy
from pathlib import Path
from transcriptor.view import TranscriptorView
from transcriptor.utils import parse_conditions, extract_job_number, get_media_duration
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
        ordination = [
            "client_id",
            "date_received",
            "id",
            "job_number",
            "job_type",
            "status",
            "date_due",
            "date_submitted",
            "total_quantity",
            "quantity",
            "job_rate",
            "amount",
            "amount_paid",
            "note",
        ]

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

        TranscriptorView().print_table(
            jobs, orientation="horizontal", ordination=ordination
        )

    show_jobs_parser.set_defaults(func=show_jobs)

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
            args.file = prompt("Enter job file path: ")

        def job_callback(job_file):
            tmp_args = copy(args)

            client_id = tmp_args.client_id
            job_number = tmp_args.job_number
            date_received = tmp_args.date_received
            date_due = tmp_args.date_due

            if not client_id:
                self.show_clients(args=None)
                client_id = int(prompt("Enter client id: "))
                tmp_args.client_id = client_id  # Update the original args

            if not job_number:
                job_number = extract_job_number(str(job_file)) or prompt(
                    "Enter job number: "
                )
                tmp_args.job_number = job_number  # Update the original args

            if not date_received:
                date_received = prompt(
                    "Enter date received: ",
                )
                tmp_args.date_received = date_received  # Update the original args
            if not date_due:
                date_due = prompt(
                    "Enter date due: ",
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
                    "Enter work on file: ",
                )
                tmp_args.work_on_file = work_on_file
            if not tmp_args.work_on_file.strip().lower().startswith("y"):
                return

            if not job_type:
                job_type = prompt(
                    "Enter job type: ",
                )
                tmp_args.job_type = job_type
            total_quantity = get_media_duration(task_file)
            if not quantity:
                quantity = prompt("Enter quantity: ", default=str(total_quantity))
                tmp_args.quantity = quantity

            if not job_template:
                job_template = prompt(
                    "Enter job template: ",
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


def main():
    from api import API
    from pathlib import Path

    api = API(base_dir=Path(__file__).parent)
    app = Transcriptor(api)
    c = TranscriptorCMD(app)
    # c = TranscriptorCMD()
    try:
        sys.exit(c.cmdloop())
    except (KeyboardInterrupt, EOFError):
        c.poutput("\n** Exiting program, bye **\n")
        return True


if __name__ == "__main__":
    main()
