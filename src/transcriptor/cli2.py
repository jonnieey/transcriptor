import cmd
import json
import os
import shlex
import textwrap
from pathlib import Path

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
    is_valid_file,
    job_file_validator,
    name_validator,
    parse_quantity,
    sc,
    template_type_validator,
    work_validator,
    yes_no_validator,
)
from transcriptor.view import ConsoleView


class TranscriptorCMD(cmd.Cmd):
    prompt = "(trans) "

    def __init__(self, app=None):
        super().__init__()
        if app is None:
            self.app = Transcriptor()
        else:
            self.app = app

    def do_EOF(self, arg):
        """
        Exit
        """
        print("\n** Exiting program, bye **\n")
        return True

    def do_help(self, arg):
        if not arg:
            return cmd.Cmd.do_help(self, arg)
        else:
            print("Custom command helpline")

    def postloop(self):
        print()

    def emptyline(self):
        pass

    def do_exit(self, arg):
        """Exit"""
        print("\n** Exiting program, bye **\n")
        return True

    def do_quit(self, arg):
        """Exit"""
        print("\n** Exiting program, bye **\n")
        return True

    def do_clear(self, arg):
        """Clear screen"""
        os.system("clear")

    def print_help(self):
        print("Usage: transcriptor <command>")

    def precmd(self, arg):
        """Capture help commands and parse method docstring using textwrap"""

        command, args, line = cmd.Cmd.parseline(self, arg)
        if command == "help" and args != "":
            eval_str = line.replace("help", "do").replace(" ", "_")
            eval_str = f"self.{eval_str}.__doc__"
            try:
                line = textwrap.dedent(eval(eval_str)).lstrip("\n")
                print(line)
            except TypeError:
                pass
            finally:
                return ""
        return line

    def config_show(self, arg):
        """
        Show configuration
        Ex.
           show config
        """
        config = self.app.config
        cols, rows = (config.cols(), config.rows())
        ConsoleView().vertical_table(cols, rows)

    def profile_show(self, arg):
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
            print("** Profile doesn't exist **.")
            return

    def clients_show(self, argv):
        """
        Show clients
        Ex.
            show clients
            show clients 1
        """
        cols = ["id", "name", "email", "normal", "expedite", "interpreted"]
        if len(argv) > 1:
            scalars = self.app.api.list_clients(argv[1])
        else:
            scalars = self.app.api.list_clients()

        if scalars:
            ConsoleView().vertical_table(cols, scalars, headers=cols)
            return 0
        else:
            print("** No Clients **")
            return 1

    def jobs_show(self, arg):
        """
        List jobs
        Ex.
            show jobs
        """
        # TODO Filter jobs with app.api.list_jobs(attributes={})
        jobs = self.app.api.list_jobs()
        total_amount, total_amount_paid = self.app.api.get_jobs_scalars_total(jobs)
        total_dict = {
            "total_amount": total_amount,
            "total_amount_paid": total_amount_paid,
        }
        ConsoleView().print_job_table(jobs, **total_dict)

    def do_show(self, arg):
        """
        Show objects
            Ex:
            >> show profile
            >> show jobs
            >> show config
        """
        if arg:
            argv = shlex.split(arg)
            klass = argv[0]
            try:
                eval(f"self.{klass}_show({argv})")
            except AttributeError:
                pass

    def yaml_update(self, argv, fields, obj):
        update_dict = {}
        invalid_fields = []

        dict_start = argv.find("{")
        dict_end = argv.rfind("}")

        if dict_start != -1 and dict_end != -1:
            dict_str = argv[dict_start : dict_end + 1]

            try:
                raw_dict = json.loads(dict_str)
                new_dict = {sc(k): v for k, v in raw_dict.items() if k in fields}
                update_dict.update(new_dict)
                obj.__dict__.update(update_dict)

            except (AttributeError, ValueError, json.decoder.JSONDecodeError) as e:
                print("Invalid dict representation")
                print(e)

            finally:
                return

        argv = shlex.split(argv)
        update_values = argv[1:]

        if len(update_values) % 2 != 0 or len(update_values) == 0:
            print("Not enough args and values")
            return

        it = iter(update_values)
        args_dict = dict(zip(it, it))

        for k, v in args_dict.items():
            if k not in fields:
                invalid_fields.append(k)
            else:
                update_dict[sc(k)] = v

        if invalid_fields != []:
            print(f"Invalid attributes:  {', '.join(invalid_fields)}")

        obj.__dict__.update(update_dict)
        eval(f"self.app.save_{argv[0]}()")

    def config_update(self, argv):
        fields = ["base-dir", "date-format"]
        obj = self.app.config
        self.yaml_update(argv, fields, obj)

    def profile_update(self, argv):
        fields = ["first-name", "last-name", "area", "country"]
        obj = self.app.profile
        self.yaml_update(argv, fields, obj)

    def client_update(self, argv):
        # update client <client-id> <attr> <attr-value> <attr> <attr-value>
        fields = ["name", "email", "rates"]
        update_dict = {}

        try:
            client_id = shlex.split(argv)[1]
            isinstance(int(client_id), int)
            update_dict["client_id"] = client_id
        except ValueError:
            print("Invalid client id, expects a number")
            return

        dict_start = argv.find("{")
        dict_end = argv.rfind("}")

        if dict_start != -1 and dict_end != -1:
            dict_str = argv[dict_start : dict_end + 1]

            try:
                raw_dict = json.loads(dict_str)
                new_dict = {sc(k): v for k, v in raw_dict.items() if k in fields}
                update_dict.update(new_dict)
                self.app.api.edit_client(**update_dict)

            except (AttributeError, ValueError, json.decoder.JSONDecodeError) as e:
                print("Invalid dict representation")
                print(e)

            finally:
                return
        else:

            argv = shlex.split(argv)
            update_values = argv[2:]

            if len(update_values) % 2 != 0 or len(update_values) == 0:
                print("Not enough args and values")
                return

            it = iter(update_values)
            args_dict = dict(zip(it, it))
            invalid_fields = []

            for k, v in args_dict.items():
                if k not in fields:
                    invalid_fields.append(k)

                if v.strip().startswith("[") and v.strip().endswith("]"):
                    try:
                        update_dict[sc(k)] = json.loads(v)
                    except json.decoder.JSONDecodeError:
                        print("Cannot convert to python object")
                        continue
                else:
                    update_dict[sc(k)] = v

            if invalid_fields != []:
                print(f"Invalid attributes:  {', '.join(invalid_fields)}")

            self.app.api.edit_client(**update_dict)

    def job_update(self, argv):
        # update job <job-id> <attr> <attr-value> <attr> <attr-value>
        fields = [
            "client-id",
            "date-received",
            "job-number",
            "job-type",
            "status",
            "date-due",
            "quantity",
            "job-rate",
            "date-submitted",
            "amount-paid",
            "note",
        ]
        update_dict = {}

        try:
            job_id = shlex.split(argv)[1]
            isinstance(int(job_id), int)
            update_dict["job_id"] = job_id
        except ValueError:
            print("Invalid job id, expects a number")
            return

        dict_start = argv.find("{")
        dict_end = argv.rfind("}")

        if dict_start != -1 and dict_end != -1:
            dict_str = argv[dict_start : dict_end + 1]

            try:
                raw_dict = json.loads(dict_str)
                new_dict = {sc(k): v for k, v in raw_dict.items() if k in fields}
                update_dict.update(new_dict)
                self.app.api.edit_job(**update_dict)

            except (AttributeError, ValueError, json.decoder.JSONDecodeError) as e:
                print("Invalid dict representation")
                print(e)

            finally:
                return

        argv = shlex.split(argv)
        update_values = argv[2:]

        if len(update_values) % 2 != 0 or len(update_values) == 0:
            print("Not enough args and values")
            return

        it = iter(update_values)
        args_dict = dict(zip(it, it))
        invalid_fields = []

        for k, v in args_dict.items():
            if k not in fields:
                invalid_fields.append(k)

            if v.strip().startswith("[") and v.strip().endswith("]"):
                try:
                    update_dict[sc(k)] = json.loads(v)
                except json.decoder.JSONDecodeError:
                    print("Cannot convert to python object")
                    continue
            else:
                update_dict[sc(k)] = v

        # if invalid_fields != []:
        #     print(f"Invalid attributes:  {', '.join(invalid_fields)}")

        self.app.api.edit_job(**update_dict)

    def do_update(self, arg):
        """
        Update objects
            Ex:
            >> update config base-dir <path-to-base-dir>
            >> update profile first-name <first name>
        """
        if arg:
            argv = shlex.split(arg)
            klass = argv[0]
            try:
                eval(f"self.{klass}_update({'arg'})")
            except AttributeError:
                pass

    def client_add(self, args):
        # name, email, rates
        try:
            name = prompt(
                "Enter Client's name: ",
                validator=name_validator,
                validate_while_typing=True,
            )

            email = prompt(
                "Enter client's email: ",
                validator=email_validator,
                validate_while_typing=True,
            )

            print("Rates:")

            rates = {
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

            self.app.add_client(name, email, rates)

        except (KeyboardInterrupt, EOFError):
            print("**")
            return True

    def job_add(self, arg):
        # add job <job-file-path>
        argv = shlex.split(arg)
        argc = len(argv)

        clients = [
            client._mapping["ClientModel"].name
            for client in self.app.api.list_clients()
        ]

        if not clients:
            print("** No clients, add clients first")
            return

        def client_exists(text):
            return text.strip().lower() in list(map(lambda x: x.lower(), clients))

        is_valid_client = Validator.from_callable(
            client_exists,
            error_message="Client doesn't exist",
            move_cursor_to_end=True,
        )

        try:
            if argc == 1:
                if self.clients_show("") == 1:
                    return
                client_name = clients[
                    int(prompt("Enter client number: ", validator=gt0_validator)) - 1
                ]
                job_file = prompt("Enter job file path: ", validator=job_file_validator)

            elif argc == 2:
                client_name = argv[1]
                job_file = prompt("Enter job file path: ", validator=job_file_validator)

            elif argc >= 3:
                if is_valid_file(argv[2]):
                    client_name = argv[1]
                    job_file = argv[2]
                else:
                    print("File does not exist")
                    return

            date_fmt = self.app.config.date_format
            date_received = prompt(
                f"Date received {date_fmt}: ", validator=date_validator
            )
            date_due = prompt(f"Date due {date_fmt}: ", validator=date_validator)

            def add_job_cb(
                media_file: str,
                client: ClientModel,
                rates: RatesModel,
                date_received: str,
                job_num: str,
                job_dir: str | Path,
            ):

                print(media_file)
                work_on_file = prompt(
                    f"Work on this file [{job_file}]: ", validator=yes_no_validator
                )
                if work_on_file.lower() == "y":
                    job_type = prompt("Specify job type: ", validator=work_validator)
                    job_rate = rates.__dict__.get(job_type.lower(), 0.40)

                    total_quantity = get_media_duration(media_file)
                    quantity = parse_quantity(
                        prompt(
                            "Enter quantity of task: ",
                            default=str(total_quantity),
                        ),
                        total_quantity,
                    )
                    job_template = prompt(
                        "Specify template type: ", validator=template_type_validator
                    )
                    note = prompt("Notes: ")

                    job_dict = {
                        "client_id": client.id,
                        "date_received": date_received,
                        "job_number": job_num,
                        "job_type": job_type,
                        "total_quantity": total_quantity,
                        "job_rate": job_rate,
                        "quantity": quantity,
                        "date_due": date_due,
                        "job_path": str(job_dir),
                        "note": note,
                    }
                    job = self.app.api.create_job(**job_dict)
                    return job, job_template

            self.app.add_job(
                add_job_cb=add_job_cb,
                client_name=client_name,
                job_file=job_file,
                date_received=date_received,
                date_due=date_due,
            )

        except (KeyboardInterrupt, EOFError):
            print("**")
            return True

    def do_add(self, arg):
        """
        Add objects
        Ex.
            add client
        """
        if arg:
            argv = shlex.split(arg)
            klass = argv[0]
            try:
                eval(f"self.{klass}_add({'arg'})")
            except AttributeError:
                pass

    def client_delete(self, arg):
        cols = ["id", "name", "email", "normal", "expedite", "interpreted"]
        argv = shlex.split(arg)

        try:
            if len(argv) > 1:
                scalars = self.app.api.list_clients(argv[1])
                ConsoleView().vertical_table(cols, scalars, headers=cols)
                client_id = int(argv[1])
            else:
                scalars = self.app.api.list_clients()
                clients = [client._mapping["ClientModel"].name for client in scalars]
                ConsoleView().vertical_table(cols, scalars, headers=cols)
                client_id = prompt("Enter client number: ", validator=gt0_validator)
                print()
                ConsoleView().vertical_table(
                    cols, self.app.api.list_clients(client_id), headers=cols
                )

            confirm = input(f"Are you sure you want to delete this client [Y/N]: ")
            if confirm.lower() == "y":
                self.app.api.delete_client(argv[1])

        except (KeyboardInterrupt, EOFError):
            print("**")
            return

    def job_delete(self, arg):
        argv = shlex.split(arg)
        job = self.app.api.get_job(argv[1])
        ConsoleView().print_job_table(job)

        confirm = input(f"Are you sure you want to delete this job [Y/N]: ")
        if confirm.lower() == "y":
            self.app.api.delete_job(argv[1])

    def do_delete(self, arg):
        """
        Delete object
        Ex.
            delete client 1
        """
        if arg:
            argv = shlex.split(arg)
            klass = argv[0]
            try:
                eval(f"self.{klass}_delete({'arg'})")
            except AttributeError:
                pass

    def do_invoice(self, arg):
        if self.clients_show("") == 1:
            return
        date_fmt = self.app.config.date_format

        try:
            client_id = prompt("Enter client number: ", validator=gt0_validator)
            period_start = prompt(f"Date from {date_fmt}: ", validator=date_validator)
            period_end = prompt(f"Date from {date_fmt}: ", validator=date_validator)

            self.app.create_invoice(
                client_id=client_id,
                period_start=period_start,
                period_end=period_end,
            )
        except (KeyboardInterrupt, EOFError):
            print("**")
            return


def main():
    try:
        TranscriptorCMD().cmdloop()
    except (KeyboardInterrupt, EOFError):
        print("\n** Exiting program, bye **\n")
        return True


if __name__ == "__main__":
    main()
