from collections import OrderedDict
from typing import Dict, List, Optional, Union

from rich.console import Console
from rich.table import Table
from sqlalchemy.engine.row import RowMapping

from transcriptor.models import Client  # type: ignore
from transcriptor.utils import tc  # type: ignore


class TranscriptorView:
    def __init__(self):
        self.console = Console()
        self.table = Table(
            show_header=True,
            header_style="bold red",
            title_justify="center",
            padding=(0, 0),
        )

    def generate_table(
        self,
        objects: Union[
            Dict[str, str],
            List[Dict[str, Optional[Union[int, str, Client, float]]]],
            List[Dict[str, Union[int, float]]],
            List[RowMapping],
            List[List[str]],
        ],
        orientation: str = "vertical",
        ordination: None = None,
    ):
        if not objects:
            return

        if isinstance(objects, dict):
            object_dict = objects
        elif isinstance(objects, (list, tuple)):
            try:
                object_dict = objects[0].__dict__
            except AttributeError:
                object_dict = objects[0]  # type: ignore

        if ordination:
            try:
                object_dict = OrderedDict(
                    [(key, object_dict[key]) for key in ordination]
                )
            except KeyError:
                object_dict = OrderedDict(object_dict)
        else:
            try:
                object_dict = OrderedDict(object_dict)
            except ValueError:
                pass

        if orientation == "vertical":
            if isinstance(objects, dict):
                columns = ["Option", "Value"]
                for column in columns:
                    self.table.add_column(tc(column))
                for option, value in object_dict.items():
                    self.table.add_row(tc(option), value)

            if isinstance(objects, (list, tuple)):
                if isinstance(object_dict, dict):
                    columns = list(object_dict.keys())
                    for column in columns:
                        self.table.add_column(tc(column))
                    for obj in objects:
                        row = [
                            str(object_dict.get(column)) for column in columns
                        ]
                    self.table.add_row(*row)

                elif isinstance(object_dict, (list, tuple)):
                    columns = object_dict
                    for column in columns:
                        self.table.add_column(tc(column))
                    for row in objects[1:]:
                        self.table.add_row(*row)

        elif orientation == "horizontal":
            columns = [
                column
                for column in object_dict.keys()
                if column
                not in (
                    "_sa_instance_state",
                    "job_path",
                    "client",
                    "job",
                    "rate",
                )
            ]
            for column in columns:
                self.table.add_column(tc(column))

            if isinstance(objects, dict):
                row = [str(object_dict.get(column)) for column in columns]
                self.table.add_row(*row)

            if isinstance(objects, (list, tuple)):
                for obj in objects:
                    try:
                        rows = [
                            [obj.__dict__[column] for column in columns]
                            for obj in objects
                        ]
                    except AttributeError:
                        rows = [
                            [obj[column] for column in columns]  # type: ignore
                            for obj in objects
                        ]
                for row in rows:
                    row = list(map(str, row))
                    self.table.add_row(*row)

                self.table.add_section()
                try:
                    try:
                        total_amount = sum(
                            [obj.get("amount") for obj in objects]  # type: ignore
                        )
                        total_amount_paid = sum(
                            [obj.get("amount_paid") for obj in objects]  # type: ignore
                        )

                        amount_column = columns.index("amount")
                        amount_paid_column = columns.index("amount_paid")

                        summary_row = [""] * len(columns)
                        summary_row[amount_column] = str(total_amount)
                        summary_row[amount_paid_column] = str(
                            total_amount_paid
                        )

                        self.table.add_row(*summary_row)
                    except (TypeError, KeyError, AttributeError):
                        total_amount = sum([obj.amount for obj in objects])  # type: ignore
                        total_amount_paid = sum([obj.amount_paid for obj in objects])  # type: ignore
                        amount_column = columns.index("amount")
                        amount_paid_column = columns.index("amount_paid")

                        summary_row = [""] * len(columns)
                        summary_row[amount_column] = str(total_amount)
                        summary_row[amount_paid_column] = str(
                            total_amount_paid
                        )
                        self.table.add_row(*summary_row)

                except AttributeError:
                    pass

    def print_table(
        self,
        objects: Union[
            Dict[str, str],
            List[Dict[str, Optional[Union[int, str, Client, float]]]],
            List[Dict[str, Union[int, float]]],
            List[RowMapping],
            List[List[str]],
        ],
        orientation: str = "vertical",
        ordination: None = None,
    ):
        self.generate_table(
            objects, orientation=orientation, ordination=ordination
        )
        self.console.print(self.table)
