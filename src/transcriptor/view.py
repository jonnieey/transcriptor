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

    def vertical_table(self, cols, rows, headers=["Option", "Value"], title=""):
        self.table.title = title

        for header in headers:
            self.table.add_column(tc(header))

        for idx, row in enumerate(rows):
            if not isinstance(row, str):
                r = row._asdict()
                self.table.add_row(*r2s(r.values()))
            else:
                self.table.add_row(tc(cols[idx]), row)
        self.console.print(self.table)

