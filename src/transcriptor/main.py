import sys

from transcriptor.cli import main as cli
from transcriptor.tui import main as tui


def main():
    try:
        if len(sys.argv) > 1:
            cli()
        else:
            tui()
    except KeyError:
        tui()


if __name__ == "__main__":
    main()
