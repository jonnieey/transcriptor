import argparse
import json
import os
import sys
from copy import copy
from datetime import datetime

import cmd2
from prompt_toolkit import prompt

from transcriptor.base import Transcriptor
from transcriptor.utils import (
    date_validator,
    email_validator,
    float_validator,
    format_date,
    get_media_duration,
    gt0_validator,
    job_file_validator,
    name_validator,
    parse_date_due,
    parse_job_number,
    str_to_date,
    template_type_validator,
    work_validator,
    yes_no_validator,
)
from transcriptor.view import ConsoleView


class StripStrAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if (
            not hasattr(namespace, self.dest)
            or getattr(namespace, self.dest) is None
        ):
            setattr(namespace, self.dest, "")

        setattr(namespace, self.dest, values.strip("'").strip('"'))


class KeyValueAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if (
            not hasattr(namespace, self.dest)
            or getattr(namespace, self.dest) is None
        ):
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
            except ValueError as e:
                raise argparse.ArgumentTypeError(
                    f"Invalid {self.dest} value: {values}"
                ) from e
            if not isinstance(value, dict):
                raise argparse.ArgumentTypeError(
                    f"{values} is must be a dictionary"
                )
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
show_profile_parser = show_subparsers.add_parser(
    "profile", help="show profile"
)
show_clients_parser = show_subparsers.add_parser(
    "clients", help="show client"
)
show_clients_parser.add_argument(
    "-w", "--where", nargs="*", help="Filter condition"
)
show_clients_parser.add_argument("-r", "--raw", help="Raw sql query")

show_jobs_parser = show_subparsers.add_parser("jobs", help="show jobs")
show_jobs_parser.add_argument(
    "-w", "--where", nargs="*", help="Filter condition"
)
show_jobs_parser.add_argument(
    "-a", "--all", action="store_true", help="Show all jobs"
)
show_jobs_parser.add_argument("-r", "--raw", help="Raw sql query")

show_cutoffs_parser = show_subparsers.add_parser(
    "cutoffs", help="show cutoffs"
)
show_rates_parser = show_subparsers.add_parser("rates", help="show rates")
show_rates_parser.add_argument("-r", "--raw", help="Raw sql query")

add_parser = base_subparsers.add_parser("add", help="add object")
add_subparsers = add_parser.add_subparsers(
    title="subcommands", help="subcommand help"
)
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
    nargs=3,
    help="client rates dict",
    default=(0.40, 0.60, 0.30),
)
add_job_parser = add_subparsers.add_parser("job", help="add job")
add_job_parser.add_argument("-c", "--client_id", type=int, help="client id")
add_job_parser.add_argument("-f", "--job-file", help="job file")
add_job_parser.add_argument("-j", "--job-num", help="job number")
add_job_parser.add_argument("-r", "--date-received", help="date received")
add_job_parser.add_argument("-d", "--date-due", help="date due")
add_job_parser.add_argument("-q", "--quantity", help="quantity")
add_job_parser.add_argument("-w", "--wof", help="work on file")
add_job_parser.add_argument("-t", "--job-type", help="job type")
add_job_parser.add_argument("-T", "--job-template", help="job template")
add_job_parser.add_argument("-N", "--note", help="job note")
add_job_parser.add_argument(
    "-P", "--no-prompt", action="store_true", help="Do not prompt"
)

update_parser = base_subparsers.add_parser("update", help="update object")
update_subparsers = update_parser.add_subparsers(
    title="subcommands", help="subcommand help"
)
update_config_parser = update_subparsers.add_parser(
    "config", help="update config"
)
update_config_parser.add_argument("-b", "--base-dir", help="base directory")
update_config_parser.add_argument("-d", "--date-format", help="date format")
update_config_parser.add_argument(
    "-p",
    "--persistent",
    action="store_true",
    help="persistent config (write to file)",
)

update_profile_parser = update_subparsers.add_parser(
    "profile", help="update profile"
)
update_profile_parser.add_argument(
    "-f", "--first-name", type=str, nargs="*", help="User first name"
)

update_profile_parser.add_argument(
    "-l", "--last-name", type=str, nargs="*", help="User last name"
)
update_profile_parser.add_argument(
    "-a", "--area", type=str, nargs="+", help="User area"
)
update_profile_parser.add_argument(
    "-c", "--country", type=str, nargs="+", help="User country"
)

update_client_parser = update_subparsers.add_parser(
    "client", help="update client"
)

update_client_parser.add_argument(
    "-s", "--set-cond", nargs="*", help="Set condition"
)
update_client_parser.add_argument(
    "-w", "--where", nargs="*", help="Filter condition"
)
update_client_parser.add_argument("-r", "--raw", help="Raw sql query")

update_jobs_parser = update_subparsers.add_parser("jobs", help="update job")
update_jobs_parser.add_argument(
    "-s", "--set-cond", nargs="*", help="Set condition"
)
update_jobs_parser.add_argument(
    "-w", "--where", nargs="*", help="Filter condition"
)
update_jobs_parser.add_argument("-r", "--raw", help="Raw sql query")

update_rates_parser = update_subparsers.add_parser(
    "rates", help="update rate"
)
update_rates_parser.add_argument(
    "-s", "--set-cond", nargs="*", help="Set condition"
)
update_rates_parser.add_argument(
    "-w", "--where", nargs="*", help="Filter condition"
)
update_rates_parser.add_argument("-r", "--raw", help="Raw sql query")

delete_parser = base_subparsers.add_parser("delete", help="delete object")
delete_subparsers = delete_parser.add_subparsers(
    title="subcommands", help="subcommand help"
)
delete_client_parser = delete_subparsers.add_parser(
    "client", help="delete client"
)
delete_client_parser.add_argument(
    "-w", "--where", nargs="*", help="Filter condition"
)
delete_client_parser.add_argument(
    "-P", "--no-prompt", action="store_true", help="Do not prompt"
)
delete_client_parser.add_argument(
    "-p", "--purge", action="store_true", help="Remove clients all files"
)
delete_client_parser.add_argument("-r", "--raw", help="Raw sql query")

delete_jobs_parser = delete_subparsers.add_parser("jobs", help="delete job")
delete_jobs_parser.add_argument(
    "-w", "--where", nargs="*", help="Filter condition"
)
delete_jobs_parser.add_argument(
    "-P", "--no-prompt", action="store_true", help="Do not prompt"
)
delete_jobs_parser.add_argument(
    "-p",
    "--purge",
    action="store_true",
    help="Remove job directory, all files",
)
delete_jobs_parser.add_argument(
    "-d", "--delete", action="store_true", help="Delete task file"
)
delete_jobs_parser.add_argument("-r", "--raw", help="Raw sql query")
delete_rates_parser = delete_subparsers.add_parser(
    "rates", help="delete rate"
)
delete_rates_parser.add_argument(
    "-w", "--where", nargs="*", help="Filter condition"
)
delete_rates_parser.add_argument("-r", "--raw", help="Raw sql query")

invoice_parser = base_subparsers.add_parser(
    "invoice", help="Invoice commands"
)
invoice_subparsers = invoice_parser.add_subparsers(
    title="subcommands", help="subcommand help"
)
create_invoice_parser = invoice_subparsers.add_parser(
    "create", help="Create Invoice"
)
create_invoice_parser.add_argument("-c", "--client-id", help="client id")

create_invoice_parser.add_argument(
    "-w", "--where", nargs="*", help="Filter criteria"
)
create_invoice_parser.add_argument(
    "-p", "--to-pdf", action="store_true", help="Create invoice PDF"
)
create_invoice_parser.add_argument(
    "-l", "--to-html", action="store_true", help="Create invoice html"
)
create_invoice_parser.add_argument("-t", "--title", help="Invoice title")
create_invoice_parser.add_argument(
    "-T", "--table", action="store_true", help="show cutoff table"
)
create_invoice_parser.add_argument(
    "-P", "--no-prompt", action="store_true", help="Do not prompt"
)
create_invoice_parser.add_argument("-r", "--raw", help="Raw sql query")

purge_files_parser = base_subparsers.add_parser(
    "purge", help="Invoice commands"
)
purge_files_subparsers = purge_files_parser.add_subparsers(
    title="subcommands", help="subcommand help"
)
purge_files_parser.add_argument(
    "-w", "--where", nargs="+", help="where conditions"
)
purge_files_parser.add_argument(
    "-P", "--no-prompt", action="store_true", help="Do not prompt"
)
purge_files_parser.add_argument("-r", "--raw", help="Raw sql query")


class TranscriptorCMD(cmd2.Cmd):
    prompt = "(trans) "

    def __init__(self, app=None):
        self.app = Transcriptor() if app is None else app
        hist_file = self.app.base_dir.joinpath(".hist")
        alias_script = self.app.config_dir.joinpath(".cmd2rc")
        super().__init__(
            persistent_history_file=hist_file,
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

    def postloop(self):
        if self.app.config_changed is True:
            c = prompt("** Config changed ** Save changes? (y/n)")
            if c.lower() == "y":
                self.app.save_config(self.app.config.__dict__)
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
        if profile := self.app.profile:
            ConsoleView().print_table(profile.__dict__)
        else:
            self.poutput("** Profile doesn't exist **.")
            return

    show_profile_parser.set_defaults(func=show_profile)

    def show_clients(self, args):
        """
        Show clients
        Ex.
           show clients
        """
        if args and args.raw:
            clients = self.app.api.get_clients(raw_statement=args.raw)
        else:
            clients = (
                self.app.api.get_clients(args.where)
                if args and args.where
                else self.app.api.get_clients()
            )
        return (
            ConsoleView().print_table(clients, orientation="hor")
            if clients
            else 1
        )

    show_clients_parser.set_defaults(func=show_clients)

    def show_jobs(self, args):
        """
        Show jobs
        Ex.
           show jobs
        """
        if args.raw:
            if jobs := self.app.api.get_jobs(raw_statement=args.raw):
                ConsoleView().print_table(jobs, orientation="hor")

        else:
            if args.all:
                args.where = []
            elif not args.where and not args.raw:
                args.where = ["status=Pending"]
            else:
                args.where = [" ".join(args.where)]
            if jobs := self.app.api.get_jobs(args.where):
                ConsoleView().print_table(jobs, orientation="hor")

    show_jobs_parser.set_defaults(func=show_jobs)

    def show_cutoffs(self, arg):
        """
        Show cutoffs
        Ex.
           show cutoffs
        """
        ConsoleView().print_table(self.app.load_cutoffs(), orientation="hor")

    show_cutoffs_parser.set_defaults(func=show_cutoffs)

    def show_rates(self, args):
        """
        Show rates
        Ex.
           show rates
        """
        if args.raw:
            ConsoleView().print_table(
                self.app.api.get_rates(raw_statement=args.raw),
                orientation="hor",
            )
        else:
            ConsoleView().print_table(
                self.app.api.get_rates(), orientation="hor"
            )

    show_rates_parser.set_defaults(func=show_rates)

    def add_client(self, args):
        """
        Add client
        Ex.
           add client -n name -e email -r rates 0.4 0.3 0.2
        """

        def parse_rates(rates):
            if not rates:
                return
            default_dict = dict(
                zip(["normal", "expedite", "interpreted"], [0.40, 0.60, 0.30])
            )
            rates_dict = dict(
                zip(["normal", "expedite", "interpreted"], rates)
            )
            return default_dict | rates_dict

        # name, email, rates
        try:

            def get_rates():
                return {
                    "normal": float(
                        prompt(
                            "    Normal: ",
                            default="0.40",
                            validator=float_validator,
                        )
                    ),
                    "expedite": float(
                        prompt(
                            "    Expedite: ",
                            default="0.60",
                            validator=float_validator,
                        )
                    ),
                    "interpreted": float(
                        prompt(
                            "    Interpreted: ",
                            default="0.30",
                            validator=float_validator,
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
            args.email = args.email or prompt(
                "Enter client's email: ",
                validator=email_validator,
                validate_while_typing=True,
            )

            args.rates = parse_rates(args.rates) or get_rates()
            self.app.create_client(args.name, args.email, args.rates)

        except (KeyboardInterrupt, EOFError):
            self.poutput("**")
            return True

    add_client_parser.set_defaults(func=add_client)

    def add_job(self, args):
        """Add job
        Ex.
           add job -f file ...
        """
        args.job_file = args.job_file or prompt(
            "Enter job file path: ", validator=job_file_validator
        )
        # copy args to avoid defaults being overwritten
        # ex. If job_dir has multiple tasks, the info on first
        # task such  as arg.quantity will apply to following
        # tasks as defaults. if arg.quantity on first task is 5,
        # the second task will have arg.quantity set to 5.
        # This is not wanted, therefore a copy is required of args with
        # no defaults.

        def job_callback(job_file):
            temp_args = copy(args)
            if not temp_args.client_id:
                if self.show_clients({}) == 1:
                    return
                temp_args.client_id = int(
                    prompt("Enter client id: ", validator=gt0_validator)
                )

            temp_args.job_num = (
                temp_args.job_num
                or parse_job_number(str(job_file))
                or prompt(
                    "Enter job number: ",
                    validator=gt0_validator,
                )
            )

            date_received = temp_args.date_received or prompt(
                "Enter date received: ",
                validator=date_validator,
                validate_while_typing=True,
                default=datetime.now().strftime(self.app.config.date_format),
            )
            date_due = temp_args.date_due or prompt(
                "Enter date due: ",
                validator=date_validator,
                validate_while_typing=True,
                default=format_date(
                    parse_date_due(temp_args.job_file),
                    self.app.config.date_format,
                ),
            )
            temp_args.date_received = str_to_date(
                date_received, self.app.config.date_format
            ).date()
            temp_args.date_due = str_to_date(
                date_due, self.app.config.date_format
            ).date()

            return {
                "client_id": temp_args.client_id,
                "job_num": temp_args.job_num,
                "date_rec": temp_args.date_received,
                "date_due": temp_args.date_due,
            }

        def task_callback(task_file):
            temp_args = copy(args)
            temp_args.wof = temp_args.wof or prompt(
                f"Work on file? ...{'/'.join(task_file.parts[-2:])}: ",
                validator=yes_no_validator,
            )
            if not temp_args.wof.strip().startswith(("y", "Y")):
                return {}
            temp_args.job_type = temp_args.job_type or prompt(
                "Enter job type: ",
                validator=work_validator,
                validate_while_typing=True,
            )

            total_quantity = get_media_duration(task_file)
            if temp_args.no_prompt and not temp_args.quantity:
                temp_args.quantity = total_quantity
            else:
                temp_args.quantity = temp_args.quantity or prompt(
                    "Enter quantity: ",
                    default=str(total_quantity),
                )
            temp_args.job_template = temp_args.job_template or prompt(
                "Enter job template: ",
                validator=template_type_validator,
            )
            temp_args.note = temp_args.note or prompt(
                "Enter notes: ", default=""
            )
            return {
                "job_type": temp_args.job_type,
                "quantity": temp_args.quantity,
                "job_template": temp_args.job_template,
                "note": temp_args.note,
                "total_quantity": total_quantity,
            }

        self.app.create_job(args.job_file, job_callback, task_callback)

    add_job_parser.set_defaults(func=add_job)
    # add_cutoffs_parser.set_defaults(func=add_cutoffs)

    def update_config(self, args):
        self.app.config.base_dir = args.base_dir or self.app.config.base_dir
        self.app.config.date_format = (
            args.date_format or self.app.config.date_format
        )
        if args.persistent:
            self.app.save_config(self.app.config.__dict__)

    def update_profile(self, args):
        excluded_keys = ["func", "cmd2_statement", "cmd2_handler"]
        profile_list = [
            (k, " ".join(v) if isinstance(v, list) else v)
            for k, v in args._get_kwargs()
            if k not in excluded_keys and v is not None
        ]

        updated_profile = {**self.app.profile.__dict__, **dict(profile_list)}
        self.app.save_profile(updated_profile)

    def update_client(self, args):
        if args.raw:
            self.app.api.update("clients", raw_statement=args.raw)
        else:
            if not args.set_cond or not args.where:
                return
            set_cond = " ".join(args.set_cond)
            where = " ".join(args.where)
            self.app.api.update("clients", [set_cond], [where])

        # self.yaml_update(arg, obj)

    def update_jobs(self, args):
        if args.raw:
            self.app.update_jobs(raw_statement=args.raw)
        else:
            if not args.set_cond or not args.where:
                return
            set_cond = " ".join(args.set_cond)
            where = " ".join(args.where)
            self.app.update_jobs(set_cond, where)

    def update_rates(self, args):
        if not args.set_cond or not args.where:
            return
        set_cond = " ".join(args.set_cond)
        where = " ".join(args.where)
        self.app.api.update("rates", [set_cond], [where])

    update_config_parser.set_defaults(func=update_config)
    update_profile_parser.set_defaults(func=update_profile)
    update_client_parser.set_defaults(func=update_client)
    update_jobs_parser.set_defaults(func=update_jobs)
    update_rates_parser.set_defaults(func=update_rates)

    def delete_client(self, args):
        clients = None
        where = None
        if args.raw and not args.no_prompt:
            clients = self.app.api.get_clients(raw_statement=args.raw)
        elif not args.raw and args.where:
            where = " ".join(args.where)
            if not args.no_prompt:
                clients = self.app.api.get_clients([where])

        if clients:
            ConsoleView().print_table(clients, orientation="hor")

            confirm = prompt(
                "Are you sure you want to delete these clients? (y/n): ",
                default="n",
            )
            if confirm.lower() == "y":
                if args.raw is not None:
                    self.app.delete_clients(
                        raw_statement=args.raw, purge=args.purge
                    )
                elif args.where is not None:
                    self.app.delete_clients(condition=where, purge=args.purge)

    delete_client_parser.set_defaults(func=delete_client)

    def delete_jobs(self, args):
        if not args.where or args.raw:
            return

        if args.raw:
            if not args.no_prompt:
                jobs = self.app.api.get_jobs(raw_statement=args.raw)
                ConsoleView().print_table(
                    jobs, orientation="hor"
                ) if jobs else ""
                confirm = prompt(
                    "Are you sure you want to delete these jobs? (y/n): ",
                    default="n",
                )
                if confirm.lower() != "y":
                    return

        else:
            if not args.no_prompt:
                jobs = self.app.api.get_jobs(args.where)
                ConsoleView().print_table(
                    jobs, orientation="hor"
                ) if jobs else ""
                confirm = prompt(
                    "Are you sure you want to delete these jobs? (y/n): ",
                    default="n",
                )
                if confirm.lower() != "y":
                    return
        self.app.delete_jobs(args.where, args.delete, args.purge)

    delete_jobs_parser.set_defaults(func=delete_jobs)

    def delete_rates(self, args):
        if not args.where:
            return
        where = " ".join(args.where)
        rates = self.app.api.get_rates([where])
        ConsoleView().print_table(rates, orientation="hor") if rates else ""
        confirm = prompt(
            "Are you sure you want to delete these rates? (y/n): ",
            default="n",
        )
        if confirm.lower() != "y":
            return
        # TODO should also cascade client
        self.app.api.delete("rates", [where])

    delete_rates_parser.set_defaults(func=delete_rates)

    def create_invoice(self, args):
        try:
            if not args.client_id and self.show_clients({}) == 1:
                return
            if args.no_prompt and not args.client_id:
                print("Error : No client id provided")
                return
            else:
                args.client_id = args.client_id or int(
                    prompt("Enter client id: ", validator=gt0_validator)
                )

            if not args.table and not args.raw:
                args.where = args.where or []
                conditions = f"client_id={args.client_id}"
                if args.where:
                    args.where.append(f" {conditions}")
                    args.where = [" ".join(args.where)]
                else:
                    args.where = [conditions]

            elif (
                not args.no_prompt
                and args.table
                and not args.where
                and not args.raw
            ):
                cutoff_list = self.app.load_cutoffs()
                for idx, row in enumerate(cutoff_list):
                    if idx == 0:
                        row.insert(0, "")
                    else:
                        row.insert(0, idx)
                ConsoleView().print_table(cutoff_list, orientation="hor")
                cutoff = int(
                    prompt(
                        "Enter DEPOSIT date number (on second column): ",
                        validator=gt0_validator,
                    )
                )
                _, start, _ = cutoff_list[cutoff - 1]
                _, end, _ = cutoff_list[cutoff]

                cutoff_condition = (
                    f"date_submitted>{start} date_submitted<={end}"
                )
                args.where = [
                    f"client_id={args.client_id} {cutoff_condition}"
                ]
            unpaid_jobs_cond = [
                "{} AND date_submitted IS NOT NULL AND amount > amount_paid".format(
                    args.raw if args.raw is not None else ""
                )
            ]

            if inv := self.app.create_invoice(
                args.client_id,
                [args.where, unpaid_jobs_cond],
                args.to_pdf,
                args.to_html,
                args.title,
            ):
                ConsoleView().console.print(inv)

        except (KeyboardInterrupt, EOFError):
            self.poutput("**")
            return

    create_invoice_parser.set_defaults(func=create_invoice)

    def purge_files(self, args):
        if not args.where and not args.raw:
            return
        if args.raw:
            jobs = self.app.api.get_jobs(raw_statement=args.raw)
        elif args.where:
            args.where = " ".join(args.where)
            jobs = self.app.api.get_jobs([args.where])
        print(args.raw)

        if not args.no_prompt:
            ConsoleView().print_table(jobs, orientation="hor") if jobs else ""
            confirm = prompt(
                "Are you sure you want to delete these job files? (y/n): ",
                default="n",
            )
            if confirm.lower() != "y":
                return
        self.app.purge_files(jobs)

    purge_files_parser.set_defaults(func=purge_files)

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

    @cmd2.with_argparser(purge_files_parser)
    def do_purge(self, args):
        """
        Purge command help
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
