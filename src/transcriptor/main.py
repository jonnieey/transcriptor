from sys import argv, exit

from transcriptor.cli import main as cli
from transcriptor.tui import main as tui
from transcriptor.utils import get_version


def main():
    if len(argv) > 1:
        if argv[1] == "--version":
            print(f"Version: {get_version()}")
            exit()
        if argv[1] == "tui":
            tui()
            exit()
    else:
        cli()


if __name__ == "__main__":
    main()
