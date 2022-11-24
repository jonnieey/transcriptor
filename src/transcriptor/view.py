from typing import Tuple

from rich.console import Console
from rich.table import Table

from transcriptor.utils import tc


def r2s(row):
    return (str(v) for v in row)


class ConsoleView:
    def __init__(self):
        self.console = Console()
        self.table = Table(
            show_header=True, header_style="bold red", title_justify="center"
        )

    def vertical_table(
        self,
        cols: Tuple[str],
        rows,
        headers: list = ["Option", "Value"],
        title: str = "",
    ):
        """
        Print vertical table in terminal

        Arguments:
            cols: tuple of strings
            rows: list of tuples
            headers: list of strings
            title: table title
        """
        self.table.title = title

        for header in headers:
            self.table.add_column(tc(header))

        for idx, row in enumerate(rows):
            if isinstance(row, str):
                self.table.add_row(tc(cols[idx]), row)
            elif isinstance(row, dict):
                self.table.add_row(*r2s(row.values()))
            else:
                r = row._asdict()
                r = {k: v for k, v in r.items() if k in cols}
                self.table.add_row(*r2s(r.values()))
        self.console.print(self.table)
