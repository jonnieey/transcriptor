import cmd
import shlex
import textwrap

from transcriptor.base import Transcriptor
from transcriptor.utils import ks
from transcriptor.view import ConsoleView

app = Transcriptor()


class TranscriptorCMD(cmd.Cmd):
    prompt = "(trans) "

    def do_EOF(self, arg):
        """
        Exit
        """
        return True

    def postloop(self):
        print()

    def emptyline(self):
        pass

    def do_exit(self, arg):
        """Exit"""
        return True

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
        Configuration actions
        """
        config = app.config
        cols, rows = (config.cols(), config.rows())
        ConsoleView().vertical_table(cols, rows)

    def profile_show(self, arg):
        profile = app.profile
        if profile:
            cols, rows = (profile.cols(), profile.rows())
            ConsoleView().vertical_table(cols, rows)

    def jobs_show(self, arg):
        jobs = app.api.list_jobs()
        total_amount, total_amount_paid = app.api.get_jobs_scalars_total(jobs)
        total_dict = {
            "total_amount": total_amount,
            "total_amount_paid": total_amount_paid,
        }
        ConsoleView().print_job_table(jobs, **total_dict)

    def clients_show(self, arg):
        cols = ["id", "name", "email", "normal", "expedite", "interpreted"]
        scalars = app.api.list_clients()
        if scalars:
            ConsoleView().vertical_table(cols, scalars, headers=cols)

    def do_show(self, arg):
        """
        Show objects
            Ex:
            >> show profile
            >> show jobs
        """
        if arg:
            argv = shlex.split(arg)
            klass = argv[0]
            eval(f"self.{klass}_show({argv})")

    def yaml_update(self, argv, fields, obj):
        argc = len(argv)
        update_values = argv[1:]

        if len(update_values) % 2 != 0 or len(update_values) == 0:
            print("Not enough args and values")
            return

        it = iter(update_values)
        args_dict = dict(zip(it, it))
        update_dict = {}
        invalid_fields = []

        for k, v in args_dict.items():
            if k not in fields:
                invalid_fields.append(k)
            else:
                update_dict[ks(k)] = v

        if invalid_fields != []:
            print(f"Invalid attributes:  {', '.join(invalid_fields)}")

        obj.__dict__.update(update_dict)
        eval(f"app.save_{argv[0]}()")

    def config_update(self, argv):
        fields = ["base-dir", "date-format"]
        obj = app.config
        self.yaml_update(argv, fields, obj)

    def profile_update(self, argv):
        fields = ["first_name", "last_name", "area", "country"]
        obj = app.profile
        self.yaml_update(argv, fields, obj)

    def client_update(self, argv):
        # update client <client-id> <attr> <attr-value> <attr> <attr-value>
        fields = ["new-name", "new-email", "new-rates"]

        argc = len(argv)

        # TODO Update controller.edit_client to use client-id
        # try:
        #     isinstance(int(argv[1]), int)
        # client_id = argv[1]
        client_name = argv[1]
        # except ValueError:
        #     print("Invalid client id, expects a number")
        #     return

        update_values = argv[2:]

        if len(update_values) % 2 != 0 or len(update_values) == 0:
            print("Not enough args and values")
            return

        it = iter(update_values)
        args_dict = dict(zip(it, it))
        update_dict = {}
        invalid_fields = []

        for k, v in args_dict.items():
            if k not in fields:
                invalid_fields.append(k)
            else:
                update_dict[ks(k)] = v

        if invalid_fields != []:
            print(f"Invalid attributes:  {', '.join(invalid_fields)}")

        update_dict["client_name"] = client_name

        app.api.edit_client(**update_dict)

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
            eval(f"self.{klass}_update({argv})")


if __name__ == "__main__":
    TranscriptorCMD().cmdloop()
