import argparse
import json
import os
import sys

import cmd2
from prompt_toolkit import prompt

from transcriptor.base import Transcriptor
from transcriptor.utils import (
    date_validator,
    email_validator,
    float_validator,
    get_media_duration,
    gt0_validator,
    job_file_validator,
    name_validator,
    parse_date_due,
    str_to_date,
    template_type_validator,
    work_validator,
)
from transcriptor.view import ConsoleView


class StripStrAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if not hasattr(namespace, self.dest) or getattr(namespace, self.dest) is None:
            setattr(namespace, self.dest, "")

        setattr(namespace, self.dest, values.strip("'").strip('"'))


class KeyValueAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if not hasattr(namespace, self.dest) or getattr(namespace, self.dest) is None:
            setattr(namespace, self.dest, {})

        if isinstance(values, list):
            values = " ".join(values)

        if "=" in values:
            pairs = values.split()
            for pair in pairs:
                key, value = pair.split("=")
                getattr(namespace, self.dest)[key] = value

        else:
            try:
                value = json.loads(values)
            except ValueError:
                raise argparse.ArgumentTypeError(f"Invalid {self.dest} value: {values}")
            if not isinstance(value, dict):
                raise argparse.ArgumentTypeError(f"{values} is must be a dictionary")
            getattr(namespace, self.dest).update(value)


base_parser = cmd2.Cmd2ArgumentParser(
    description="Transcriptor CLI",
)
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
show_clients_parser.add_argument("-v", "--key-val", nargs="*", help="Show clients")
show_jobs_parser = show_subparsers.add_parser("jobs", help="show jobs")
show_jobs_parser.add_argument("-v", "--key-val", nargs="*", help="Show jobs")
show_jobs_parser.add_argument("-a", "--all", action="store_true", help="Show all jobs")
# show_cutoffs_parser = show_subparsers.add_parser("cutoffs", help="show cutoffs")

add_parser = base_subparsers.add_parser("add", help="add object")
add_subparsers = add_parser.add_subparsers(title="subcommands", help="subcommand help")
add_client_parser = add_subparsers.add_parser("client", help="add client")
add_client_parser.add_argument(
    "-n", "--name", type=str, action=StripStrAction, help="client name"
)

add_client_parser.add_argument(
    "-e",
    "--email",
    type=str,
    action=StripStrAction,
    help="client email",
)
add_client_parser.add_argument(
    "-r",
    "--rates",
    action=KeyValueAction,
    help="client rates dict",
    default={"normal": 0.40, "expedite": 0.60, "interpreted": 0.30},
)
add_job_parser = add_subparsers.add_parser("job", help="add job")
add_job_parser.add_argument("-c", "--client_id", type=int, help="client id")
add_job_parser.add_argument("-f", "--job-file", help="job file")
add_job_parser.add_argument("-r", "--date-received", help="date received")
add_job_parser.add_argument("-d", "--date-due", help="date due")
add_job_parser.add_argument("-q", "--quantity", help="quantity")
add_job_parser.add_argument("-w", "--wof", help="work on file")
add_job_parser.add_argument("-t", "--job-type", help="job type")
add_job_parser.add_argument("-T", "--job-template", help="job template")
add_job_parser.add_argument("-N", "--note", help="job note")


class TranscriptorCMD(cmd2.Cmd):
    prompt = "(trans) "

    def __init__(self, app=None):
        super().__init__()
        if app is None:
            self.app = Transcriptor()
        else:
            self.app = app

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

    def postloop(self):
        self.poutput()

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
        ConsoleView().print_table(config.__dict__)

    show_config_parser.set_defaults(func=show_config)

    def show_profile(self, arg):
        """
        Show profile
        Ex.
           show profile
        """
        profile = self.app.profile
        if profile:
            ConsoleView().print_table(profile.__dict__)
        else:
            self.poutput("** Profile doesn't exist **.")
            return

    show_profile_parser.set_defaults(func=show_profile)

    def show_clients(self, args):
        clients = self.app.api.get_clients(args.key_val)
        if clients:
            ConsoleView().print_table(clients, orientation="hor")
            return 0
        return 1

    show_clients_parser.set_defaults(func=show_clients)

    def show_jobs(self, args):
        if args.all:
            args.key_val = []
        elif not args.key_val and not args.all:
            args.key_val = ["status=Pending"]
        jobs = self.app.api.get_jobs(args.key_val)
        if jobs:
            ConsoleView().print_table(jobs, orientation="hor")

    #
    show_jobs_parser.set_defaults(func=show_jobs)
    # show_cutoffs_parser.set_defaults(func=show_cutoffs)

    def add_client(self, args):
        # name, email, rates
        try:
            get_rates = lambda: {
                "normal": float(
                    prompt("    Normal: ", default="0.40", validator=float_validator)
                ),
                "expedite": float(
                    prompt("    Expedite: ", default="0.60", validator=float_validator)
                ),
                "interpreted": float(
                    prompt(
                        "    Interpreted: ", default="0.30", validator=float_validator
                    )
                ),
            }

            # if not args.name:
            args.name = args.name or prompt(
                "Enter Client's name: ",
                validator=name_validator,
                validate_while_typing=True,
            )

            # if args.email is None:
            args.email = prompt(
                "Enter client's email: ",
                validator=email_validator,
                validate_while_typing=True,
            )

            self.poutput("Rates:")
            args.rates = get_rates()
            self.app.create_client(args.name, args.email, args.rates)

        except (KeyboardInterrupt, EOFError):
            self.poutput("**")
            return True

    add_client_parser.set_defaults(func=add_client)

    def add_job(self, args):
        args.job_file = args.job_file or prompt(
            "Enter job file path: ", validator=job_file_validator
        )

        def job_callback(job_file):
            if not args.client_id:
                if self.show_clients("") == 1:
                    return
                args.client_id = int(
                    prompt("Enter client id: ", validator=gt0_validator)
                )

            date_received = args.date_received or prompt(
                "Enter date received: ",
                validator=date_validator,
                validate_while_typing=True,
            )
            date_due = (
                args.date_due
                or parse_date_due(args.job_file)
                or prompt(
                    "Enter date due: ",
                    validator=date_validator,
                    validate_while_typing=True,
                )
            )
            args.date_received = str_to_date(
                date_received, self.app.config.date_format
            ).date()
            args.date_due = str_to_date(date_due, self.app.config.date_format).date()

            return {
                "client_id": args.client_id,
                "date_rec": args.date_received,
                "date_due": args.date_due,
            }

        def task_callback(task_file):
            args.job_type = args.job_type or prompt(
                "Enter job type: ",
                validator=work_validator,
                validate_while_typing=True,
            )

            total_quantity = get_media_duration(task_file)
            args.quantity = args.quantity or prompt(
                "Enter quantity: ",
                default=str(total_quantity),
            )
            args.job_template = args.job_template or prompt(
                "Enter job template: ",
                validator=template_type_validator,
            )
            args.note = args.note or prompt("Enter notes: ", default="")
            return {
                "job_type": args.job_type,
                "quantity": args.quantity,
                "job_template": args.job_template,
                "note": args.note,
                "total_quantity": total_quantity,
            }

        self.app.create_job(args.job_file, job_callback, task_callback)

    add_job_parser.set_defaults(func=add_job)
    # add_cutoffs_parser.set_defaults(func=add_cutoffs)

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
    c = TranscriptorCMD()
    try:
        sys.exit(c.cmdloop())
    except (KeyboardInterrupt, EOFError):
        c.poutput("\n** Exiting program, bye **\n")
        return True


if __name__ == "__main__":
    main()
