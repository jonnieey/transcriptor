from rich.console import Console
from rich.table import Table

from transcriptor.utils import tc


class ConsoleView:
    def __init__(self):
        self.console = Console()
        self.table = Table(
            show_header=True, header_style="bold red", title_justify="center"
        )

    def print_table(self, data: dict | list, orientation: str = "vert") -> None:
        """
        Print a table

        Arguments:
            data: Data to print
            orientation: Orientation of the table (vert or hor)
        """
        if not data:
            return
        if orientation == "vert":
            for column in ["Option", "Value"]:
                self.table.add_column(tc(column))
            if isinstance(data, dict):
                for option, value in data.items():
                    self.table.add_row(tc(option), value)
            elif isinstance(data, (list, tuple)):
                for row in data:
                    for option, value in row.items():
                        self.table.add_row(tc(option), value)

        elif orientation == "hor":
            if isinstance(data, dict):
                columns = data.keys()
                rows = data.values()
            elif isinstance(data, (list, tuple)):
                try:
                    columns = data[0].keys()
                    rows = data
                except AttributeError as e:
                    columns = data[0]
                    rows = data[1:]

            for column in columns:
                self.table.add_column(tc(column))
            for idx, row in enumerate(rows):
                try:
                    row_values = list(map(str, row.values()))
                    self.table.add_row(*row_values)
                except AttributeError as e:
                    self.table.add_row(*row)

        self.console.print(self.table)
