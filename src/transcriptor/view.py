from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple, Union

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

    def _get_attr(self, obj: Any, attr: str, default: Any = None) -> Any:
        """Helper to get attribute from dict or object."""
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)

    def generate_table(
        self,
        objects: Union[Dict, List, Tuple],
        orientation: str = "vertical",
        ordination: Optional[List[str]] = None,
    ):
        if not objects:
            return

        # Prepare data for processing
        if isinstance(objects, dict):
            data_list = [objects]
        else:
            data_list = list(objects)

        first_item = data_list[0]
        if ordination:
            columns = ordination
        else:
            if isinstance(first_item, dict):
                columns = list(first_item.keys())
            elif isinstance(first_item, (list, tuple)):
                columns = first_item  # Header row
                data_list = data_list[1:]
            else:
                columns = [
                    c
                    for c in first_item.__dict__.keys()
                    if not c.startswith("_")
                ]

        if orientation == "vertical":
            self.table.add_column(tc("Option"))
            self.table.add_column(tc("Value"))
            # For vertical, show key-value pairs of the first item
            for col in columns:
                val = self._get_attr(first_item, col)
                self.table.add_row(tc(col), str(val))

        elif orientation == "horizontal":
            filtered_columns = [
                col
                for col in columns
                if col
                not in (
                    "_sa_instance_state",
                    "job_path",
                    "client",
                    "job",
                    "rate",
                    "client_email",
                )
            ]
            for col in filtered_columns:
                self.table.add_column(tc(col))

            total_amount = 0.0
            total_paid = 0.0
            has_totals = False

            for item in data_list:
                style = self._get_item_style(item)
                if isinstance(item, (list, tuple)):
                    row = [str(x) for x in item]
                else:
                    row = [
                        str(self._get_attr(item, col, ""))
                        for col in filtered_columns
                    ]
                self.table.add_row(*row, style=style)

                # Accumulate totals if columns exist
                amount = self._get_attr(item, "amount")
                paid = self._get_attr(item, "amount_paid")
                if amount is not None:
                    total_amount += float(amount)
                    has_totals = True
                if paid is not None:
                    total_paid += float(paid)
                    has_totals = True

            if has_totals:
                self.table.add_section()
                summary_row = [""] * len(filtered_columns)
                if "amount" in filtered_columns:
                    summary_row[
                        filtered_columns.index("amount")
                    ] = f"{total_amount:.2f}"
                if "amount_paid" in filtered_columns:
                    summary_row[
                        filtered_columns.index("amount_paid")
                    ] = f"{total_paid:.2f}"
                self.table.add_row(*summary_row)

    def _get_item_style(self, item: Any) -> Optional[str]:
        date_submitted = self._get_attr(item, "date_submitted")
        date_due = self._get_attr(item, "date_due")
        amount = self._get_attr(item, "amount")
        amount_paid = self._get_attr(item, "amount_paid")

        if date_submitted:
            if (
                amount is not None
                and amount_paid is not None
                and float(amount_paid) < float(amount)
            ):
                return "blue"
            return "white"

        if date_due:
            if isinstance(date_due, str):
                try:
                    date_due = datetime.strptime(date_due, "%Y-%m-%d").date()
                except ValueError:
                    return None

            if isinstance(date_due, datetime):
                date_due = date_due.date()

            if isinstance(date_due, date):
                days_left = (date_due - date.today()).days
                if days_left < 0:
                    return "purple"
                if days_left < 2:
                    return "red"
                if days_left < 4:
                    return "yellow"
                return "green"
        return None

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
