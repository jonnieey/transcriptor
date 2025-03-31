from sys import argv, exit

from transcriptor.cli import main as cli
from transcriptor.utils import get_version


def main():
    if len(argv) > 1 and argv[1] == "--version":
        print(f"Version: {get_version()}")
        exit()
    cli()


if __name__ == "__main__":
    main()
