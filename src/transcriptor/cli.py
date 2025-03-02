from transcriptor.base import Transcriptor
import os
import sys
import cmd2
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
show_profile_parser = show_subparsers.add_parser("profile", help="show profile")
show_clients_parser = show_subparsers.add_parser("clients", help="show client")
show_rates_parser = show_subparsers.add_parser("rates", help="show rates")
show_jobs_parser = show_subparsers.add_parser("jobs", help="show jobs")


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
        jobs = self.app.api.get_jobs()
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


def main():
    c = TranscriptorCMD()
    try:
        sys.exit(c.cmdloop())
    except (KeyboardInterrupt, EOFError):
        c.poutput("\n** Exiting program, bye **\n")
        return True


if __name__ == "__main__":
    main()
