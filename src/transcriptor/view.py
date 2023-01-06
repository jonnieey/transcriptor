from collections import OrderedDict
from typing import Tuple

from rich.console import Console
from rich.table import Table

from transcriptor.utils import tc


def r2s(row):
    return (str(v) for v in row)


class ConsoleView:
    def __init__(self):
        self.console = Console()
        self.table = Table(
            show_header=True,
            header_style="bold red",
            title_justify="center",
        )

    def print_job_table(self, job_scalars, **kwargs):
        job_objects = [job._mapping["JobModel"] for job in job_scalars]
        total_amount = kwargs.get("total_amount", None)
        total_amount_paid = kwargs.get("total_amount_paid", None)

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
            "job_path",
            "note",
        ]
        [self.table.add_column(tc(h)) for h in headers_list]
        for idx, job in enumerate(job_objects):
            job_dict = job.__dict__
            job_dict.pop("_sa_instance_state")
            # job_dict.pop("id")
            r = sorted(job_dict.items(), key=lambda t: headers_list.index(t[0]))
            self.table.add_row(*r2s([x[1] for x in r]))

        if total_amount or total_amount_paid:
            total_row = []
            for h in headers_list:
                if h == "amount":
                    total_row.append(str(total_amount))
                elif h == "amount_paid":
                    total_row.append(str(total_amount_paid))
                else:
                    total_row.append("")
            total_row[0] = "TOTAL"
            self.table.add_row()
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
            self.table.add_column(tc(header))

        for idx, row in enumerate(rows):
            if isinstance(row, str):
                self.table.add_row(tc(cols[idx]), row)
            elif isinstance(row, dict):
                self.table.add_row(*r2s(row.values()))
            else:
                r = row._asdict()
                r = {k: v for k, v in r.items() if k in cols}
                self.table.add_row(*r2s(r.values()))
        self.console.print(self.table)
