import contextlib

from rich.console import Console
from rich.table import Table

from transcriptor.utils import tc


class ConsoleView:
    def __init__(self):
        self.console = Console()
        self.table = Table(
            show_header=True,
            header_style="bold red",
            title_justify="center",
            padding=(0, 0),
        )

    def generate_table(self, columns, rows):
        # TODO let user choose to show job path in table
        try:
            col_amount = columns.index("amount")
            col_amount_paid = columns.index("amount_paid")
            total_amount = 0
            total_amount_paid = 0
            jobs_table = True
        except ValueError:
            jobs_table = False

        for column in columns:
            self.table.add_column(tc(column))
        for row in rows:
            if jobs_table:
                total_amount += row[col_amount]
                total_amount_paid += row[col_amount_paid]
            row = list(map(str, row))
            self.table.add_row(*row)

        if jobs_table:
            self.table.add_section()
            summary_row = [""] * len(columns)
            summary_row[col_amount] = str(round(total_amount, 2))
            summary_row[col_amount_paid] = str(round(total_amount_paid, 2))
            self.table.add_row(*summary_row)

    def print_table(
        self, data: dict | list, orientation: str = "vert"
    ) -> None:
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
                columns = list(data.keys())
                with contextlib.suppress(ValueError):
                    columns.remove("job_path")
                rows = [data[column] for column in columns]
            elif isinstance(data, (list, tuple)):
                try:
                    columns = list(data[0].keys())
                    with contextlib.suppress(ValueError):
                        columns.remove("job_path")
                    rows = [
                        [row[column] for column in columns] for row in data
                    ]
                    self.generate_table(columns, rows)
                except AttributeError:
                    columns = data[0]
                    rows = data[1:]
                    self.generate_table(columns, rows)

        self.console.print(self.table)
