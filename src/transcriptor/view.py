from datetime import datetime
from typing import Tuple

from rich.console import Console
from rich.table import Table
from rich.text import Text
from sqlalchemy.engine.row import Row

from transcriptor.utils import tc


class ConsoleView:
    def __init__(self):
        self.console = Console()
        self.table = Table(
            show_header=True, header_style="bold red", title_justify="center"
        )

    def print_job_table(self, job_scalars, **kwargs):
        job_objects = [job._mapping["JobModel"] for job in job_scalars]
        total_amount = kwargs.get("total_amount")
        total_amount_paid = kwargs.get("total_amount_paid")
        self.table.title = "Job Table"

        headers_list = [
            "client_id",
            "date_received",
            "id",
            "job_number",
            "job_type",
            "status",
            "date_due",
            "total_quantity",
            "quantity",
            "job_rate",
            "date_submitted",
            "amount",
            "amount_paid",
            # "job_path",
            "note",
        ]
        for header in headers_list:
            self.table.add_column(tc(header))

        for row_idx, job in enumerate(job_objects):
            job_dict = job.__dict__
            job_dict.pop("_sa_instance_state", None)
            row = [str(job_dict.get(header, "")) for header in headers_list]
            self.table.add_row(*row)

        if total_amount is not None or total_amount_paid is not None:
            total_row = ["TOTAL"]
            for header in headers_list[1:]:
                if header == "amount":
                    total_row.append(str(total_amount))
                elif header == "amount_paid":
                    total_row.append(str(total_amount_paid))
                else:
                    total_row.append("")
            self.table.add_section()
            self.table.add_row(*total_row)

        self.console.print(self.table)

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
            self.table.add_column(Text(header))

        for idx, row in enumerate(rows):
            if isinstance(row, Row):
                client_dict = {**row[1].__dict__, **row[0].__dict__}
                client_dict.pop("_sa_instance_state", None)
                client_dict.pop("rates_id", None)
                client_sorted_dict = sorted(
                    client_dict.items(), key=lambda t: headers.index(t[0])
                )
                self.table.add_row(*[Text(str(x[1])) for x in client_sorted_dict])

            elif isinstance(row, str):
                self.table.add_row(Text(tc(cols[idx])), Text(row))

            elif isinstance(row, dict):
                self.table.add_row(*[Text(str(x)) for x in row.values()])

            elif isinstance(row, tuple):
                r_dict = {k: v for k, v in zip(cols, row) if k in cols}
                self.table.add_row(*[Text(str(x[1])) for x in r_dict.items()])

        self.console.print(self.table)

    def print_cutoff_table(self, list_of_rows):
        """
        Print cutoff table in terminal

        Arguments:
            list_of_rows: list of tuples [(cutoff_date, deposit_date)]. First
            tuple is contains csv header (CUTOFF DATE, DEPOSIT DATE)

        """
        if not list_of_rows:
            return

        table = self.table
        headers = ["", *list_of_rows[0]]
        rows = list_of_rows[1:]
        today = datetime.today()
        for idx, row in enumerate(rows):
            if datetime.strptime(row[0], "%Y-%m-%d") >= today:
                color_row = idx
                break

        for column in headers:
            table.add_column(tc(column))

        for idx, row in enumerate(rows):
            table.add_row(str(idx + 1), row[0], row[1])
        table.rows[color_row].style = "red"
        self.console.print(table)
