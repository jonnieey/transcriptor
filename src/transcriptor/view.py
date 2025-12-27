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
            header_style="bold #bd93f9",
            border_style="#6272a4",
            title_style="bold #ff79c6",
            caption_style="#6272a4",
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
        title: Optional[str] = None,
    ):
        if not objects:
            return

        if title:
            self.table.title = title

        # Prepare data for processing
        if isinstance(objects, dict):
            data_list = [objects]
            is_list_of_lists = False
        elif (
            isinstance(objects, (list, tuple))
            and objects
            and isinstance(objects[0], (list, tuple))
        ):
            header = objects[0]
            data_list = objects[1:]
            columns = header
            is_list_of_lists = True
        else:
            data_list = list(objects)
            is_list_of_lists = False

        if not is_list_of_lists:
            first_item = data_list[0] if data_list else {}
            if ordination:
                columns = ordination
            else:
                if isinstance(first_item, dict):
                    columns = list(first_item.keys())
                else:
                    columns = [
                        c
                        for c in getattr(first_item, "__dict__", {}).keys()
                        if not c.startswith("_")
                    ]

        if orientation == "vertical":
            self.table.add_column(tc("Option"), style="#8be9fd")
            self.table.add_column(tc("Value"), style="#f8f8f2")

            for item in data_list:
                for col in columns:
                    if is_list_of_lists:
                        # For list of lists in vertical mode, this might be weird
                        # but let's support it by showing all items
                        try:
                            val = item[columns.index(col)]
                        except (ValueError, IndexError):
                            val = ""
                    else:
                        val = self._get_attr(item, col)
                    self.table.add_row(tc(str(col)), str(val))
                if len(data_list) > 1:
                    self.table.add_section()

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
                self.table.add_column(tc(str(col)))

            total_amount = 0.0
            total_paid = 0.0
            total_sum = 0.0
            total_job_count = 0
            has_totals = False

            for item in data_list:
                style = (
                    self._get_item_style(item)
                    if not is_list_of_lists
                    else "#f8f8f2"
                )

                if is_list_of_lists:
                    try:
                        row = [
                            str(item[columns.index(col)])
                            for col in filtered_columns
                        ]
                    except (ValueError, IndexError):
                        row = [""] * len(filtered_columns)
                else:
                    row = [
                        str(self._get_attr(item, col, ""))
                        for col in filtered_columns
                    ]

                self.table.add_row(*row, style=style)

                if not is_list_of_lists:
                    # Accumulate totals if columns exist
                    amount = self._get_attr(item, "amount")
                    paid = self._get_attr(item, "amount_paid")
                    total = self._get_attr(item, "total")
                    job_count = self._get_attr(item, "job_count")

                    if amount is not None:
                        total_amount += float(amount)
                        has_totals = True
                    if paid is not None:
                        total_paid += float(paid)
                        has_totals = True
                    if total is not None:
                        total_sum += float(total)
                        has_totals = True
                    if job_count is not None:
                        total_job_count += int(job_count)
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
                if "total" in filtered_columns:
                    summary_row[
                        filtered_columns.index("total")
                    ] = f"{total_sum:.2f}"
                if "job_count" in filtered_columns:
                    summary_row[filtered_columns.index("job_count")] = str(
                        total_job_count
                    )
                self.table.add_row(*summary_row)

    def _get_item_style(self, item: Any) -> str:
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
                return "#8be9fd"
            return "#f8f8f2"

        if date_due:
            if isinstance(date_due, str):
                try:
                    date_due = datetime.strptime(date_due, "%Y-%m-%d").date()
                except ValueError:
                    return "#f8f8f2"

            if isinstance(date_due, datetime):
                date_due = date_due.date()

            if isinstance(date_due, date):
                days_left = (date_due - date.today()).days
                if days_left < 0:
                    return "#bd93f9"
                if days_left < 2:
                    return "#ff5555"
                if days_left < 4:
                    return "#f1fa8c"
                return "#50fa7b"
        return "#f8f8f2"

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
        title: Optional[str] = None,
    ):
        self.generate_table(
            objects,
            orientation=orientation,
            ordination=ordination,
            title=title,
        )
        self.console.print(self.table)
