import argparse
from sys import exit

from transcriptor.cli import main as cli_main
from transcriptor.tui import main as tui_main
from transcriptor.utils import get_version


def main():
    parser = argparse.ArgumentParser(
        description="Transcriptor CLI application. Transcribe audio files and manage transcriptions."
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {get_version()}"
    )

    subparsers = parser.add_subparsers(
        dest="command", help="Available commands"
    )

    # TUI command
    tui_parser = subparsers.add_parser(
        "tui", help="Run the Terminal User Interface"
    )
    tui_parser.set_defaults(func=tui_main)

    # Default CLI command (if no subcommand is given)
    cli_parser = subparsers.add_parser(
        "cli", help="Run the command-line interface (default)"
    )
    cli_parser.add_argument(
        "cli_args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass to the CLI",
    )
    cli_parser.set_defaults(func=cli_main)

    args = parser.parse_args()

    if hasattr(args, "func"):
        if args.command == "cli":
            args.func(argv=args.cli_args)
        else:
            args.func()
    elif (
        args.command is None
    ):  # If no subcommand is specified, run the default CLI
        cli_main()
    else:
        parser.print_help()
        exit(1)


if __name__ == "__main__":
    main()
