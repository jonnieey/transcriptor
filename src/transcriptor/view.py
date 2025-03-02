from collections import OrderedDict
from rich.console import Console
from rich.table import Table
from transcriptor.utils import tc


class TranscriptorView:
    def __init__(self):
        self.console = Console()
        self.table = Table(
            show_header=True,
            header_style="bold red",
            title_justify="center",
            padding=(0, 0),
        )

    def generate_table(self, objects, orientation="vertical", ordination=None):
        if not objects:
            return

        if isinstance(objects, dict):
            object_dict = objects
        elif isinstance(objects, (list, tuple)):
            object_dict = objects[0].__dict__

        if ordination:
            try:
                object_dict = OrderedDict(
                    [(key, object_dict[key]) for key in ordination]
                )
            except KeyError:
                object_dict = OrderedDict(object_dict)
        else:
            object_dict = OrderedDict(object_dict)

        columns = [
            column
            for column in object_dict.keys()
            if column not in ("_sa_instance_state", "job_path")
        ]
        for column in columns:
            self.table.add_column(tc(column))

        if isinstance(objects, dict):
            row = [str(object_dict.get(column)) for column in columns]
            self.table.add_row(*row)

        if orientation == "vertical":
            if isinstance(objects, (list, tuple)):
                for obj in objects:
                    row = [str(object_dict.get(column)) for column in columns]

                self.table.add_row(*row)

        elif orientation == "horizontal":
            if isinstance(objects, (list, tuple)):
                for obj in objects:
                    rows = [
                        [obj.__dict__[column] for column in columns] for obj in objects
                    ]
                for row in rows:
                    row = list(map(str, row))
                    self.table.add_row(*row)

                self.table.add_section()
                try:
                    total_amount = sum([obj.amount for obj in objects])
                    total_amount_paid = sum([obj.amount_paid for obj in objects])

                    amount_column = columns.index("amount")
                    amount_paid_column = columns.index("amount_paid")

                    summary_row = [""] * len(columns)
                    summary_row[amount_column] = str(total_amount)
                    summary_row[amount_paid_column] = str(total_amount_paid)

                    self.table.add_row(*summary_row)
                except AttributeError:
                    pass

    def print_table(self, objects, orientation="vertical", ordination=None):
        self.generate_table(objects, orientation=orientation, ordination=ordination)
        self.console.print(self.table)
