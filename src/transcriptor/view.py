from collections import OrderedDict
from datetime import date, datetime
from typing import Dict, List, Optional, Union

from rich.console import Console
from rich.style import Style
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
                    style = None
                    try:
                        date_submitted = obj.date_submitted
                        date_due = obj.date_due
                    except AttributeError:
                        date_submitted = obj.get("date_submitted")
                        date_due = obj.get("date_due")

                    if date_submitted:
                        try:
                            amount = obj.amount
                            amount_paid = obj.amount_paid
                        except AttributeError:
                            amount = obj.get("amount")
                            amount_paid = obj.get("amount_paid")

                        if (
                            amount is not None
                            and amount_paid is not None
                            and amount_paid < amount
                        ):
                            style = "blue"
                        else:
                            style = "white"
                    elif date_due:
                        if isinstance(date_due, str):
                            try:
                                date_due = datetime.strptime(
                                    date_due, "%Y-%m-%d"
                                ).date()
                            except ValueError:
                                # Handle other potential date formats if necessary
                                pass
                        if isinstance(date_due, datetime):
                            date_due = date_due.date()
                        days_left = (date_due - date.today()).days
                        if days_left < 0:
                            style = "purple"
                        elif days_left < 2:
                            style = "red"
                        elif days_left < 4:
                            style = "yellow"
                        else:
                            style = "green"

                    try:
                        row = [
                            str(obj.__dict__[column]) for column in columns
                        ]
                    except AttributeError:
                        row = [str(obj.get(column, "")) for column in columns]
                    self.table.add_row(*row, style=style)

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
                        summary_row[amount_column] = f"{total_amount:.2f}"
                        summary_row[
                            amount_paid_column
                        ] = f"{total_amount_paid:.2f}"

                        self.table.add_row(*summary_row)
                    except (TypeError, KeyError, AttributeError):
                        total_amount = sum([obj.amount for obj in objects])  # type: ignore
                        total_amount_paid = sum([obj.amount_paid for obj in objects])  # type: ignore
                        amount_column = columns.index("amount")
                        amount_paid_column = columns.index("amount_paid")

                        summary_row = [""] * len(columns)
                        summary_row[amount_column] = f"{total_amount:.2f}"
                        summary_row[
                            amount_paid_column
                        ] = f"{total_amount_paid:2f}"
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
