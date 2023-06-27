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

        # TODO let user choose to show job path in table
        def generate_table(columns, rows):
            for column in columns:
                self.table.add_column(tc(column))
            for idx, row in enumerate(rows):
                row = list(map(str, row))
                self.table.add_row(*row)

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
                columns = list(data.keys())
                try:
                    columns.remove("job_path")
                except ValueError:
                    pass
                rows = [data[column] for column in columns]
            elif isinstance(data, (list, tuple)):
                try:
                    columns = list(data[0].keys())
                    try:
                        columns.remove("job_path")
                    except ValueError:
                        pass
                    rows = [[row[column] for column in columns] for row in data]
                    generate_table(columns, rows)
                except AttributeError as e:
                    columns = data[0]
                    rows = data[1:]
                    generate_table(columns, rows)

        self.console.print(self.table)
