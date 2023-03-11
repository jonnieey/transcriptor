import argparse
import json
import os
import sys
from pathlib import Path

import cmd2
from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator

from transcriptor.base import Transcriptor
from transcriptor.models import ClientModel, RatesModel
from transcriptor.utils import (
    date_validator,
    email_validator,
    float_validator,
    get_media_duration,
    gt0_validator,
    job_file_validator,
    name_validator,
    parse_quantity,
    template_type_validator,
    work_validator,
    yes_no_validator,
)
from transcriptor.view import ConsoleView


class KeyValueAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if not hasattr(namespace, self.dest) or getattr(namespace, self.dest) is None:
            setattr(namespace, self.dest, {})

        if "=" in values:
            pairs = values.split()
            for pair in pairs:
                key, value = pair.split("=")
                getattr(namespace, self.dest)[key] = float(value)

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
show_clients_parser = show_subparsers.add_parser("clients", help="show client")
show_clients_parser.add_argument("-i", "--id", type=int, help="client id")
show_config_parser = show_subparsers.add_parser("config", help="show config")
show_profile_parser = show_subparsers.add_parser("profile", help="show profile")
show_jobs_parser = show_subparsers.add_parser("jobs", help="show jobs")
show_jobs_parser.add_argument("-n", "--job-number", type=int, help="job number")

add_parser = base_subparsers.add_parser("add", help="add object")
add_subparsers = add_parser.add_subparsers(title="subcommands", help="subcommand help")
add_client_parser = add_subparsers.add_parser("client", help="add client")
add_client_parser.add_argument("-n", "--name", type=str, help="client name")

add_client_parser.add_argument(
    "-e",
    "--email",
    type=str,
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
add_job_parser.add_argument("-c", "--client", help="client name")
add_job_parser.add_argument("-f", "--job-file", help="job file")
add_job_parser.add_argument("-r", "--date-received", help="date received")
add_job_parser.add_argument("-d", "--date-due", help="date due")
add_job_parser.add_argument("-q", "--quantity", help="quantity")
add_job_parser.add_argument("-w", "--wof", help="work on file", default="y")
add_job_parser.add_argument("-t", "--job-type", help="job type")
add_job_parser.add_argument("-T", "--job-template", help="job template")
add_job_parser.add_argument("-N", "--note", help="job note", default=" ")

update_parser = base_subparsers.add_parser("update", help="update object")
update_subparsers = update_parser.add_subparsers(
    title="subcommands", help="subcommand help"
)
update_config_parser = update_subparsers.add_parser("config", help="update config")
update_config_parser.add_argument("-b", "--base-dir", help="base directory")
update_config_parser.add_argument("-d", "--date-format", help="date format")
update_profile_parser = update_subparsers.add_parser("profile", help="update profile")
update_profile_parser.add_argument(
    "-f", "--first-name", type=str, help="User first name"
)

update_profile_parser.add_argument("-l", "--last-name", type=str, help="User last name")
update_profile_parser.add_argument("-a", "--area", type=str, help="User area")
update_profile_parser.add_argument("-c", "--country", type=str, help="User country")

update_client_parser = update_subparsers.add_parser("client", help="update client")

update_client_parser.add_argument(
    "-i", "--client-id", type=int, help="client id to update"
)

update_client_parser.add_argument("-n", "--name", type=str, help="client name")
update_client_parser.add_argument("-e", "--email", type=str, help="client email")
update_client_parser.add_argument(
    "-r",
    "--rates",
    action=KeyValueAction,
    help="client rates dict",
)

update_job_parser = update_subparsers.add_parser("job", help="update job")
#         ]
update_job_parser.add_argument("-i", "--job-id", type=int, help="job id to update")

update_job_parser.add_argument("-c", "--client-id", help="client id")
update_job_parser.add_argument("-r", "--date-received", help="date received")
update_job_parser.add_argument("-n", "--job-number", type=int, help="job number")
update_job_parser.add_argument("-t", "--job-type", type=str, help="job type")
update_job_parser.add_argument("-s", "--status", type=str, help="job status")
update_job_parser.add_argument("-d", "--date-due", help="date due")
update_job_parser.add_argument("-q", "--quantity", help="quantity")
update_job_parser.add_argument("-R", "--job-rate", type=float, help="job rate")
update_job_parser.add_argument("-S", "--date-submitted", help="date submitted")
update_job_parser.add_argument("-a", "--amount-paid", type=float, help="amount paid")
update_job_parser.add_argument("-N", "--note", type=str, help="note")
update_job_parser.add_argument("-p", "--job-path", help="job path")

delete_parser = base_subparsers.add_parser("delete", help="delete object")
delete_subparsers = delete_parser.add_subparsers(
    title="subcommands", help="subcommand help"
)
delete_client_parser = delete_subparsers.add_parser("client", help="delete client")
delete_client_parser.add_argument("-i", "--client-id", type=int, help="client id")
delete_job_parser = delete_subparsers.add_parser("job", help="delete job")
delete_job_parser.add_argument("-i", "--job-id", type=int, help="job id")

invoice_parser = base_subparsers.add_parser("invoice", help="Invoice commands")
invoice_subparsers = invoice_parser.add_subparsers(
    title="subcommands", help="subcommand help"
)
create_invoice_parser = invoice_subparsers.add_parser("create", help="Create Invoice")
create_invoice_parser.add_argument("-c", "--client-id", help="client id")
create_invoice_parser.add_argument("-s", "--period-start", help="Period start")
create_invoice_parser.add_argument("-e", "--period-end", help="Period end")
create_invoice_parser.add_argument(
    "-f", "--to-file", action="store_true", help="Period end"
)


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

    def show_config(self, args):
        """
        Show configuration
        Ex.
           show config
        """
        config = self.app.config
        cols, rows = (config.cols(), config.rows())
        ConsoleView().vertical_table(cols, rows)

    def show_profile(self, arg):
        """
        Show profile
        Ex.
           show profile
        """
        profile = self.app.profile
        if profile:
            cols, rows = (profile.cols(), profile.rows())
            ConsoleView().vertical_table(cols, rows)
        else:
            self.poutput("** Profile doesn't exist **.")
            return

    def show_clients(self, args):

        cols = ["id", "name", "email", "normal", "expedite", "interpreted"]

        if not args or args == "" or not args.id:
            clients = self.app.api.list_clients()
            if clients:
                ConsoleView().vertical_table(cols, clients, headers=cols)
                return 0
            else:
                self.poutput("** No clients found **")
                return 1

        else:
            if args.id:
                client = self.app.api.list_clients(args.id)
                if client:
                    ConsoleView().vertical_table(cols, client, headers=cols)
                    return 0
                else:
                    self.poutput("** Client not found **")
                    return 1

    def show_jobs(self, arg):
        """
        List jobs
        Ex.
            show jobs
        """
        # TODO Filter jobs with app.api.list_jobs(attributes={})
        jobs = self.app.api.list_jobs()
        if jobs:
            total_amount, total_amount_paid = self.app.api.get_jobs_scalars_total(jobs)
            total_dict = {
                "total_amount": total_amount,
                "total_amount_paid": total_amount_paid,
            }
            ConsoleView().print_job_table(jobs, **total_dict)
            return 0
        else:
            self.poutput("** No Jobs **")
            return 1

    show_config_parser.set_defaults(func=show_config)
    show_profile_parser.set_defaults(func=show_profile)
    show_clients_parser.set_defaults(func=show_clients)
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
        # name, email, rates
        try:
            pn = lambda: prompt(
                "Enter Client's name: ",
                validator=name_validator,
                validate_while_typing=True,
            )

            pe = lambda: prompt(
                "Enter client's email: ",
                validator=email_validator,
                validate_while_typing=True,
            )

            pr = lambda: {
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

            if not args.name:
                args.name = pn()

            if args.email is None:
                args.email = pe()

            if not args.rates:
                self.poutput("Rates:")
                args.rates = pr()

            self.app.add_client(args.name, args.email, args.rates)

        except (KeyboardInterrupt, EOFError):
            self.poutput("**")
            return True

    def add_job(self, arg):

        clients = [
            client._mapping["ClientModel"].name
            for client in self.app.api.list_clients()
        ]

        if not clients:
            self.poutput("** No clients, add clients first")
            return

        def client_exists(text):
            return text.strip().lower() in list(map(lambda x: x.lower(), clients))

        is_valid_client = Validator.from_callable(
            client_exists,
            error_message="Client doesn't exist",
            move_cursor_to_end=True,
        )

        try:
            if not arg.client or arg.client not in clients:
                if self.show_clients("") == 1:
                    return
                arg.client = clients[
                    int(prompt("Enter client number: ", validator=gt0_validator)) - 1
                ]
            arg.job_file = arg.job_file or prompt(
                "Enter job file path: ", validator=job_file_validator
            )

            date_fmt = self.app.config.date_format

            arg.date_received = arg.date_received or prompt(
                f"Date received {date_fmt}: ", validator=date_validator
            )
            arg.date_due = arg.date_due or prompt(
                f"Date due {date_fmt}: ", validator=date_validator
            )

            def add_job_cb(
                media_file: str,
                client: ClientModel,
                rates: RatesModel,
                date_received: str,
                job_num: str,
                job_dir: str | Path,
            ):

                self.poutput(media_file)
                arg.wof = arg.wof or prompt(
                    f"Work on this file [{media_file}]: ", validator=yes_no_validator
                )
                if arg.wof.lower() == "y":
                    arg.job_type = arg.job_type or prompt(
                        "Specify job type: ", validator=work_validator
                    )
                    job_rate = rates.__dict__[arg.job_type.lower()]

                    total_quantity = get_media_duration(media_file)
                    arg.quantity = arg.quantity or prompt(
                        "Enter quantity of task: ",
                        default=str(total_quantity),
                    )
                    if arg.quantity.lower() in ["full", "whole"]:
                        arg.quantity = total_quantity
                    else:
                        arg.quantity = parse_quantity(arg.quantity, total_quantity)

                    arg.job_template = arg.job_template or prompt(
                        "Specify template type: ", validator=template_type_validator
                    )
                    arg.note = arg.note or prompt("Notes: ")

                    job_dict = {
                        "client_id": client.id,
                        "date_received": arg.date_received,
                        "job_number": job_num,
                        "job_type": arg.job_type,
                        "total_quantity": total_quantity,
                        "job_rate": job_rate,
                        "quantity": arg.quantity,
                        "date_due": arg.date_due,
                        "job_path": str(job_dir),
                        "note": arg.note,
                    }
                    job = self.app.api.create_job(**job_dict)
                    return job, arg.job_template

            # TODO use client id instead of client-name
            self.app.add_job(
                add_job_cb=add_job_cb,
                client_name=arg.client,
                job_file=arg.job_file,
                date_received=arg.date_received,
                date_due=arg.date_due,
            )

        except (KeyboardInterrupt, EOFError):
            self.poutput("**")
            return True

    add_client_parser.set_defaults(func=add_client)
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

    def yaml_update(self, arg, obj):
        args_list = arg.cmd2_statement.__dict__[
            "_Cmd2AttributeWrapper__attribute"
        ].arg_list
        if args_list:
            command = args_list[0]
            args = update_parser.parse_args(args_list)
            args_dict = {k: v for k, v in vars(args).items() if v is not None}
            if args_dict:
                args_dict.pop("func") if "func" in args_dict else None
                obj.__dict__.update(args_dict)
                eval(f"self.app.save_{command}()")

    def update_config(self, arg):
        obj = self.app.config
        self.yaml_update(arg, obj)

    def update_profile(self, arg):
        obj = self.app.profile
        self.yaml_update(arg, obj)

    def update_client(self, arg):
        # update client <client-id> <attr> <attr-value> <attr> <attr-value>
        try:
            if not arg.client_id:
                if self.show_clients("") == 1:
                    return
                arg.client_id = prompt("Enter client id: ", validator=gt0_validator)
            if hasattr(arg, "__dict__"):
                update_dict = {
                    k: v
                    for k, v in arg.__dict__.items()
                    if not k.startswith("cmd2") and k != "func" and v is not None
                }

            self.app.api.edit_client(**update_dict)
        except (KeyboardInterrupt, EOFError):
            self.poutput("**")
            return

    def update_job(self, arg):
        # update job <job-id> <attr> <attr-value> <attr> <attr-value>
        try:
            if not arg.job_id:
                if self.show_jobs("") == 1:
                    return
                arg.job_id = prompt("Enter job id: ", validator=gt0_validator)

            if hasattr(arg, "__dict__"):
                update_dict = {
                    k: v
                    for k, v in arg.__dict__.items()
                    if not k.startswith("cmd2") and k != "func" and v is not None
                }

            self.app.api.edit_job(**update_dict)

        except (KeyboardInterrupt, EOFError):
            self.poutput("**")
            return

    update_config_parser.set_defaults(func=update_config)
    update_profile_parser.set_defaults(func=update_profile)
    update_client_parser.set_defaults(func=update_client)
    update_job_parser.set_defaults(func=update_job)

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

    def delete_client(self, arg):

        cols = ["id", "name", "email", "normal", "expedite", "interpreted"]

        if not arg.client_id:
            if self.show_clients("") == 1:
                return
            arg.client_id = prompt("Enter client id: ", validator=gt0_validator)

        try:
            scalars = self.app.api.list_clients(arg.client_id)
            ConsoleView().vertical_table(cols, scalars, headers=cols)

            confirm_delete = prompt(
                "Are you sure you want to delete this client [Y/N]: ",
                validator=yes_no_validator,
            )
            if confirm_delete.lower() == "y":
                self.app.api.delete_client(arg.client_id)

        except (KeyboardInterrupt, EOFError):
            self.poutput("**")
            return

    def delete_job(self, arg):
        if not arg.job_id:
            if self.show_jobs("") == 1:
                return
            arg.job_id = prompt("Enter job id: ", validator=gt0_validator)
        try:
            jobs = self.app.api.list_jobs({"id": arg.job_id})
            ConsoleView().print_job_table(jobs)

            confirm_delete = prompt(
                "Are you sure you want to delete this job [Y/N]: ",
                validator=yes_no_validator,
            )
            if confirm_delete.lower() == "y":
                self.app.api.delete_job(arg.job_id)

        except (KeyboardInterrupt, EOFError):
            self.poutput("**")
            return

    delete_client_parser.set_defaults(func=delete_client)
    delete_job_parser.set_defaults(func=delete_job)

    @cmd2.with_argparser(delete_parser)
    def do_delete(self, args):
        """
        delete command help
        """
        func = getattr(args, "func", None)
        if func is not None:
            func(self, args)
        else:
            self.do_help("base")

    def create_invoice(self, arg):
        try:
            if not arg.client_id:
                if self.show_clients("") == 1:
                    return
                arg.client_id = prompt("Enter client id: ", validator=gt0_validator)

            date_fmt = self.app.config.date_format

            arg.period_start = arg.period_start or prompt(
                f"Date from {date_fmt}: ", validator=date_validator
            )
            arg.period_end = arg.period_end or prompt(
                f"Date from {date_fmt}: ", validator=date_validator
            )

            self.app.create_invoice(
                client_id=arg.client_id,
                period_start=arg.period_start,
                period_end=arg.period_end,
                to_file=arg.to_file,
            )
        except (KeyboardInterrupt, EOFError):
            self.poutput("**")
            return

    create_invoice_parser.set_defaults(func=create_invoice)

    @cmd2.with_argparser(create_invoice_parser)
    def do_invoice(self, args):
        """
        Invoice command help
        """
        func = getattr(args, "func", None)
        if func is not None:
            func(self, args)
        else:
            self.do_help("base")


#
def main():
    c = TranscriptorCMD()
    try:
        sys.exit(c.cmdloop())
    except (KeyboardInterrupt, EOFError):
        c.poutput("\n** Exiting program, bye **\n")
        return True


if __name__ == "__main__":
    main()
