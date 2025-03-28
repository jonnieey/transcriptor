import csv
import shutil
import zipfile
from datetime import date, datetime
from os import PathLike
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

from platformdirs import user_config_dir, user_data_dir
from sqlalchemy.engine.row import RowMapping

from transcriptor.api import API
from transcriptor.models import (
    Config,
    Invoice,
    InvoiceLine,
    Profile,
    SummaryInvoice,
    SummaryInvoiceLine,
)
from transcriptor.utils import (
    TEMPLATE_MAPPING,
    extract_table_data_from_docx,
    get_media_files,
    html_to_md,
    htmlstr_to_pdf,
    next_non_existent_file,
    parse_sql_update_query,
    render_invoice,
    render_summary_invoice,
    round_up,
    sc,
)
from transcriptor.utils import str_to_date as std
from transcriptor.utils import to_date_object

APP_NAME = "transcriptor"
CONFIG_FILE_NAME = "config.yaml"

DEFAULT_CONFIG = {
    "base_dir": f"{user_data_dir(APP_NAME)}",
    "date_format": "%Y-%m-%d",
}


class Transcriptor:
    def __init__(
        self,
        api: Optional[API] = None,
        config: Optional[Config] = None,
        config_file: Optional[Union[str, Path]] = None,
    ) -> None:
        """Initialize Transcriptor with optional configuration.

        Args:
            api: Optional API instance to use
            config: Optional Config object
            config_file: Optional path to config file
        """
        self._init_config(config, config_file)
        self._init_profile()
        self._init_api(api)

    def _init_config(
        self,
        config: Optional[Config],
        config_file: Optional[Union[str, Path]],
    ) -> None:
        """Initialize configuration from file or defaults."""
        self.CONFIG_DIR, self.CONFIG_FILE = self._get_config_paths(
            config_file
        )
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        if config is None:
            if not self._config_file_exists():
                self.config = Config(**DEFAULT_CONFIG)
                self._write_config()
            else:
                self.config = self._load_config()
        else:
            self.config = config
            self._write_config()

        self.base_dir = Path(self.config.base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.date_format = self.config.date_format

    def _get_config_paths(
        self, config_file: Optional[Union[str, Path]]
    ) -> tuple[Path, Path]:
        """Determine config directory and file paths."""
        if config_file is None:
            config_dir = Path(user_config_dir(APP_NAME))
            config_file = config_dir / CONFIG_FILE_NAME
        else:
            config_file = Path(config_file)
            config_dir = config_file.parent
            if not config_dir.exists():
                config_dir.mkdir(parents=True)
        return config_dir, config_file

    def _config_file_exists(self) -> bool:
        """Check if config file exists and is not empty."""
        return (
            self.CONFIG_FILE.exists() and self.CONFIG_FILE.stat().st_size > 0
        )

    def _write_config(self) -> None:
        """Write current config to file."""
        try:
            self.config.write(self.CONFIG_FILE)
        except Exception as e:
            raise RuntimeError(
                f"Failed to write config to {self.CONFIG_FILE}"
            ) from e

    def _load_config(self) -> Config:
        """Load config from file."""
        try:
            return Config.from_yaml(self.CONFIG_FILE)
        except Exception as e:
            raise RuntimeError(
                f"Failed to load config from {self.CONFIG_FILE}"
            ) from e

    def _init_profile(self) -> None:
        """Initialize profile from file or defaults."""
        self.PROFILE_FILE = self.base_dir / "profile.yaml"

        if not self._profile_file_exists():
            self.profile = Profile()
            self._write_profile()
        else:
            self.profile = self._load_profile()

    def _profile_file_exists(self) -> bool:
        """Check if profile file exists and is not empty."""
        return (
            self.PROFILE_FILE.exists()
            and self.PROFILE_FILE.stat().st_size > 0
        )

    def _write_profile(self) -> None:
        """Write current profile to file."""
        try:
            self.profile.write(self.PROFILE_FILE)
        except Exception as e:
            raise RuntimeError(
                f"Failed to write profile to {self.PROFILE_FILE}"
            ) from e

    def _load_profile(self) -> Profile:
        """Load profile from file."""
        try:
            return Profile.from_yaml(self.PROFILE_FILE)
        except Exception as e:
            raise RuntimeError(
                f"Failed to load profile from {self.PROFILE_FILE}"
            ) from e

    def _init_api(self, api: Optional[API]) -> None:
        """Initialize API instance."""
        self.api = api if api is not None else API(base_dir=self.base_dir)

    def save_config(self, yaml_file=None):
        if not yaml_file:
            yaml_file = self.CONFIG_FILE
        self.config.write(yaml_file)

    def save_profile(self, yaml_file=None):
        if not yaml_file:
            yaml_file = self.PROFILE_FILE
        self.profile.write(yaml_file)

    def create_client(
        self, name: str, email: str, rates_dict: Optional[dict] = None
    ):
        client_dict = {"name": name, "email": email}
        client_id = self.api.add_client(client_dict)
        if rates_dict is None:
            rates_dict = {
                "normal": 0.4,
                "expedite": 0.6,
                "interpreted": 0.3,
                "client_id": client_id,
            }
        else:
            # Ensure the client_id is always included in rates if provided
            rates_dict["client_id"] = client_id

        self.api.add_rates(rates_dict)
        CLIENT_DIR = self.base_dir / "clients" / sc(name)
        CLIENT_DIR.mkdir(parents=True, exist_ok=True)

        TEMPLATE_DIR = Path(__file__).parent / "templates"
        shutil.copytree(
            TEMPLATE_DIR,
            CLIENT_DIR / "templates",
            dirs_exist_ok=True,
        )

    def create_job_dir(
        self,
        client_name: str,
        job_number: str,
        date_received: str,
        date_due: str,
    ) -> Path:
        """
        Create a job directory

        Arguments:
            client_name: Client name
            job_num: Job number
            date_rec: Date received
            date_due: Date due

        Returns:
            Job directory path object
        """
        date_received_obj = std(date_received, self.date_format)
        date_due_obj = std(date_due, self.date_format)

        job_dir = (
            self.base_dir
            / "clients"
            / sc(client_name)
            / f"{date_received_obj.year}"
            / f"{date_received_obj.strftime('%B')}"
            / f"{date_received_obj.strftime('%d_%a')}_{job_number}_DUE_{date_due_obj.strftime('%d_%a')}"
        )
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir

    @staticmethod
    def mv_extract_job_file(
        job_file: Path | str, job_dir: Path | str
    ) -> None:
        """
        Move/Extract job file to jobs directory

        Arguments:
            job_file: Path object or path-like string to job file
            job_dir: Path object or path-like string to job directory
        """
        job_file = Path(job_file)
        if zipfile.is_zipfile(job_file):
            try:
                with zipfile.ZipFile(job_file) as zf:
                    zf.extractall(job_dir)
                job_file.unlink(missing_ok=True)
            except Exception as e:
                print("Could not extract zip file ->", e)

        else:
            # shutil.move(job_file, job_dir)
            shutil.copy(job_file, job_dir)

    def select_job_template(self, client: str, template: str) -> Path:
        """
        Select a job template for a task

        Arguments:
            client: Client name
            template: Template name initials

        Returns:
            Path to template file
        """
        client_template_dir = (
            self.base_dir / "clients" / sc(client) / "templates"
        )

        if not client_template_dir.exists():
            jobs_templates_path = Path(__file__).parent / "templates"
            shutil.copytree(
                jobs_templates_path, client_template_dir, dirs_exist_ok=True
            )

        return client_template_dir / TEMPLATE_MAPPING[template]

    def create_job(
        self, job_file: str, job_callback: Callable, task_callback: Callable
    ):
        """
        job callback should return a dict
        {
            "client_id": client_id,
            "job_number": job_num,
            "date_received": date_received,
            "date_due": date_due,
        }

        task callback should return a dict
        {
            "job_type": job_type,
            "quantity": quantity,
            "job_template": job_template,
            "note": note,
            "total_quantity": total_quantity
        }
        """
        if isinstance(job_file, str):
            job_file = job_file.strip("'\"")
        job_info = job_callback(job_file)
        client_query = self.api.get_clients(
            conditions={"id": [("=", job_info["client_id"])]}
        )
        if not client_query:
            print("No client found")
            return
        client = client_query[0]
        job_dir = self.create_job_dir(
            client["name"],
            job_info["job_number"],
            job_info["date_received"],
            job_info["date_due"],
        )
        self.mv_extract_job_file(job_file, job_dir)
        task_files = get_media_files(job_dir)

        tasks = []
        for task_file in task_files:
            task_info = task_callback(task_file)
            if not task_info:
                continue
            task_info.update(job_info)

            task_template_path = self.select_job_template(
                client["name"], task_info["job_template"]
            )
            task_template_suffix = task_template_path.suffix

            date_due = std(task_info["date_due"], self.date_format)
            job_number = job_info["job_number"]
            task_file_path = next_non_existent_file(
                job_dir
                / f"{job_number} Due {date_due.strftime('%m.%d')}{task_template_suffix}"
            )
            shutil.copy(task_template_path, task_file_path)

            task_rate_obj = self.api.get_rates(
                conditions={"client_id": [("=", client["id"])]}
            )
            task_info["job_rate"] = task_rate_obj[0].get(
                task_info["job_type"].lower()
            )
            task_info["amount"] = round_up(
                float(task_info["job_rate"]) * float(task_info["quantity"])
            )

            task_dict = {
                "client_id": client["id"],
                "date_received": job_info["date_received"],
                "job_number": job_info["job_number"],
                "status": "Pending",
                "amount": task_info["amount"],
                "job_type": task_info["job_type"],
                "date_due": job_info["date_due"],
                "total_quantity": task_info["total_quantity"],
                "quantity": task_info["quantity"],
                "job_rate": task_info["job_rate"],
                "job_path": f"{task_file}",
                "note": task_info["note"],
            }
            tasks.append(task_dict)
        if tasks:
            self.api.add_jobs(tasks)

    def update_jobs(self, conditions=None, values=None, raw_sql_stmt=None):

        # TODO api function accept conditions as a list, raw_sql_stmt as a string
        def _get_where_clause_from_update_sql(raw_sql_stmt):
            if raw_sql_stmt:
                where_clause = raw_sql_stmt.lower().find("where")
                if where_clause != -1:
                    where_clause = raw_sql_stmt[where_clause:]
                    where_clause = where_clause.replace(
                        "id", "job_id"
                    ).strip()
                else:
                    where_clause = None

                return where_clause
            return None

        def _get_client_to_update(conditions, values, raw_sql_stmt):
            update_client_name = ""

            if conditions:
                if values.get("client_id"):
                    update_client = self.api.get_clients(
                        conditions={"id": [("=", values["client_id"])]}
                    )
                    if update_client:
                        update_client_name = update_client[0].get("name")
                        return update_client_name
            elif raw_sql_stmt:
                set_clause, where_clause = parse_sql_update_query(
                    raw_sql_stmt
                )
                if set_clause.get("client_id"):
                    update_client = self.api.get_clients(
                        raw_sql_stmt="WHERE id = {}".format(
                            set_clause["client_id"]
                        )
                    )
                    if update_client:
                        update_client_name = update_client[0].get("name")
                        return update_client_name

        def _create_new_job_path(
            job, conditions, values, raw_sql_stmt, update_client_name
        ):
            if not update_client_name:
                update_client = job.get("client")
                update_client_name = getattr(
                    update_client, "name", update_client
                )

            task_path = Path(job["job_path"])
            old_job_path = task_path.parent
            task_name = task_path.name
            if conditions:
                date_received = values.get(
                    "date_received", job.get("date_received")
                )
                date_due = values.get("date_due", job.get("date_due"))

            elif raw_sql_stmt:
                set_clause, _ = parse_sql_update_query(raw_sql_stmt)
                date_received = set_clause.get(
                    "date_received", job.get("date_received")
                )
                date_due = set_clause.get("date_due", job.get("date_due"))

            new_job_path = self.create_job_dir(
                update_client_name,
                job["job_number"],
                date_received,
                date_due,
            )
            return old_job_path, new_job_path, task_name

        def _update_db_and_create_dir(
            conditions,
            values,
            raw_sql_stmt,
            old_job_path,
            new_job_path,
            task_name,
        ):
            keys_to_check = ("date_received", "date_due", "client_id")
            should_update_dir = any(
                key in values for key in keys_to_check
            ) or any(key in raw_sql_stmt for key in keys_to_check)
            if conditions:
                if new_job_path != old_job_path and should_update_dir:
                    values["job_path"] = f"{new_job_path}/{task_name}"
                self.api.update_jobs(conditions=conditions, values=values)
            elif raw_sql_stmt:
                if new_job_path != old_job_path and should_update_dir:
                    set_idx = raw_sql_stmt.lower().find("set ")
                    if set_idx != -1:
                        raw_sql_stmt = (
                            raw_sql_stmt[:set_idx]
                            + f'set job_path="{new_job_path}/{task_name}", '
                            + raw_sql_stmt[set_idx + len("set ") :]
                        )
                self.api.update_jobs(raw_sql_stmt=raw_sql_stmt)

            if new_job_path != old_job_path and should_update_dir:
                try:
                    new_job_path.mkdir(exist_ok=True, parents=True)
                    for item in old_job_path.iterdir():
                        item.rename(new_job_path / item.name)
                    old_job_path.rmdir()
                except ValueError:
                    raise ValueError(
                        f"{old_job_path} and {new_job_path} are the same. Cannot rename."
                    )

        def _apply_update(conditions, values, raw_sql_stmt):
            where_clause = _get_where_clause_from_update_sql(raw_sql_stmt)

            jobs = self.api.get_jobs(
                conditions=conditions, raw_sql_stmt=where_clause
            )
            if conditions is None:
                conditions = []
            if values is None:
                values = {}
            if raw_sql_stmt is None:
                raw_sql_stmt = ""

            update_client_name = _get_client_to_update(
                conditions, values, raw_sql_stmt
            )

            for job in jobs:
                if jobs:
                    (
                        old_job_path,
                        new_job_path,
                        task_name,
                    ) = _create_new_job_path(
                        job,
                        conditions,
                        values,
                        raw_sql_stmt,
                        update_client_name,
                    )
                _update_db_and_create_dir(
                    conditions,
                    values,
                    raw_sql_stmt,
                    old_job_path,
                    new_job_path,
                    task_name,
                )

        _apply_update(conditions, values, raw_sql_stmt)

    def delete_clients(
        self,
        conditions: Optional[Dict[str, List[Tuple[str, str]]]] = None,
        raw_sql_stmt: None = None,
        purge: bool = False,
    ) -> Sequence[RowMapping]:
        clients = self.api.delete_clients(
            conditions=conditions, raw_sql_stmt=raw_sql_stmt
        )
        if purge:
            for client in clients:
                client_dir = self.base_dir / "clients" / sc(client["name"])
                if client_dir.exists():
                    shutil.rmtree(client_dir)
        return clients

    def delete_jobs(self, conditions=None, raw_sql_stmt=None, purge=False):
        jobs = self.api.delete_jobs(
            conditions=conditions, raw_sql_stmt=raw_sql_stmt
        )
        if purge:
            for job in jobs:
                job_path = Path(job["job_path"])
                shutil.rmtree(job_path.parent)
        return jobs

    def read_invoice_counter(self, invoice_num_counter_file: Path) -> int:
        try:
            with open(invoice_num_counter_file, "r") as file:
                invoice_number = int(file.read())
        except FileNotFoundError:
            invoice_number = 0
        return invoice_number

    def increase_invoice_counter(self, invoice_num_counter_file):
        try:
            with open(invoice_num_counter_file, "r+") as file:
                try:
                    current_invoice_num = int(file.read())
                except ValueError:
                    current_invoice_num = 1
                file.seek(0)
                file.write(f"{current_invoice_num + 1:05}")
                file.truncate()

        except FileNotFoundError:
            invoice_number = 1
            with open(invoice_num_counter_file, "w") as file:
                file.write(f"{invoice_number:05}")

    def generate_invoice(
        self,
        client_id: str,
        conditions: Optional[Dict[str, List[Tuple[str, Any]]]] = None,
        raw_sql_stmt: None = None,
        invoice_theme: Optional[str] = None,
    ) -> Tuple[str, Union[int, Any, str, float, None]]:
        if client_id is None:
            print("CLIENT ID CANNOT BE NONE")
            return ("", "")

        if conditions:
            # Use a direct assignment or setdefault to avoid multiple dictionary updates
            conditions.setdefault("client_id", [("=", client_id)])
            conditions["amount_paid"] = [("=", 0)]
        elif raw_sql_stmt:
            # Use format strings cautiously against SQL injection; ensure client_id is validated
            if "client_id" not in raw_sql_stmt:
                raw_sql_stmt = f"""
                    {raw_sql_stmt} AND client_id = {client_id}
                    AND amount_paid = 0
                    """
            else:
                raw_sql_stmt = f"{raw_sql_stmt} AND amount_paid = 0"

        jobs = self.api.get_jobs(
            conditions=conditions, raw_sql_stmt=raw_sql_stmt
        )  # type: ignore
        if not jobs:
            print("No jobs found")
            return ("", "")

        invoice_lines = [InvoiceLine.parse_obj(job) for job in jobs]
        client = jobs[0].get("client")
        client_name = (
            client.name if hasattr(client, "name") else client
        )  # type: ignore

        INVOICE_DIR = (
            self.base_dir / "clients" / sc(client_name) / "invoices"
        )  # type: ignore
        INVOICE_NUM_COUNTER_FILE = INVOICE_DIR / "invoice_number_counter"

        invoice_number = self.read_invoice_counter(INVOICE_NUM_COUNTER_FILE)

        invoice = Invoice(
            profile=self.profile,
            invoice_number=f"{invoice_number + 1:05}",
            client_name=client_name,
            jobs=invoice_lines,
        )
        html = render_invoice(
            invoice=invoice, template_name=f"invoice_{invoice_theme}.html"
        )

        return html, client_name

    def generate_summary_invoice(
        self, client_id: str, previous_year_cutoff: None = None
    ) -> Tuple[str, Union[int, Any, str, float, None]]:
        client_name = None
        cutoffs = self.load_cutoffs(as_str=True)

        if client_id is None:
            print("CLIENT ID CANNOT BE NONE")
            return ("", "")

        jobs_by_month: dict[str, list[Any]] = {
            str(i): [] for i in range(1, 13)
        }

        cutoffs_list = list(cutoffs[1:])

        for idx, (cutoff, deposit_date) in enumerate(cutoffs_list, start=1):
            previous_cutoff, cutoff = self.select_cutoff_period(idx)
            if previous_cutoff is None:
                previous_cutoff = previous_year_cutoff or date(
                    datetime.now().year, 1, 1
                )

            conditions = {
                "client_id": [("=", client_id)],
                "amount_paid": [(">", 0)],
                "date_submitted": [
                    (">=", previous_cutoff) if previous_cutoff else None,
                    ("<=", cutoff) if cutoff else None,
                ],
            }
            conditions["date_submitted"] = [
                c
                for c in conditions["date_submitted"]  # type: ignore
                if c  # type: ignore
            ]

            jobs = self.api.get_jobs(conditions=conditions)  # type: ignore
            if jobs:
                if client_name is None:
                    client = jobs[0].get("client")
                    client_name = (
                        client.name if hasattr(client, "name") else client
                    )  # type: ignore
                month_idx = std(deposit_date, "%Y-%m-%d").month
                jobs_by_month[str(month_idx)].extend(jobs)

        months_summary_list = []
        for idx in range(1, 13):
            month = str(idx)
            jobs = jobs_by_month[month]

            month_info = {
                "month": date(
                    year=datetime.now().year, month=idx, day=1
                ).strftime("%B"),
                "job_count": len(jobs),
                "total": round(sum(job["amount_paid"] for job in jobs), 2),
            }
            months_summary_list.append(
                SummaryInvoiceLine.parse_obj(month_info)
            )

        summary_invoice = SummaryInvoice(
            profile=self.profile,
            client_name=client_name,
            summary_lines=months_summary_list,
        )
        html = render_summary_invoice(summary_invoice=summary_invoice)

        return html, client_name

    def html_to_pdf(
        self, html, client_name, output_file=None, summary_invoice=False
    ):
        INVOICE_DIR = self.base_dir / "clients" / sc(client_name) / "invoices"

        if not INVOICE_DIR.exists():
            INVOICE_DIR.mkdir(parents=True, exist_ok=True)

        date_str = date.today().strftime("%Y-%m-%d")
        client_name_sc = sc(client_name)
        file_type = "summary" if summary_invoice else "invoice"

        INVOICE_FILE = (
            INVOICE_DIR / f"{date_str}_{client_name_sc}_{file_type}.pdf"
        )

        htmlstr_to_pdf(html, output_path=INVOICE_FILE)

        if summary_invoice is False:
            INVOICE_NUM_COUNTER_FILE = INVOICE_DIR / "invoice_number_counter"
            self.increase_invoice_counter(INVOICE_NUM_COUNTER_FILE)

    def to_md(self, html: str) -> str:
        return html_to_md(html)

    def generate_cutoff_list_from_docx(
        self, docx_path: str, date_fmt: str = ""
    ) -> List[Union[Tuple[date, ...], List[str]]]:
        date_fmt = date_fmt or "%m/%d/%Y"
        cutoff_list = extract_table_data_from_docx(docx_path)

        header, *rows = cutoff_list
        cutoffs = [header] + [to_date_object(row, date_fmt) for row in rows]
        return cutoffs

    def save_cutoffs(
        self,
        cutoffs: List[Union[List[str], Tuple[date, date]]],
        file_path: Optional[
            Union[Union[str, bytes, PathLike[str], PathLike[bytes]], int]
        ] = None,
        year: Optional[Union[str | int]] = None,
    ):
        CUTOFFS_DIR = self.base_dir / "cutoffs"
        CUTOFFS_DIR.mkdir(parents=True, exist_ok=True)

        year = year or date.today().year

        file_path = (
            file_path or CUTOFFS_DIR / f"cutoffs_{year}.csv"
        )  # type: ignore
        with open(file_path, "w", newline="") as fd:
            writer = csv.writer(fd)
            writer.writerows(cutoffs)

    def load_cutoffs(
        self,
        file_path: Optional[
            Union[Union[str, bytes, PathLike[str], PathLike[bytes]], int]
        ] = None,
        date_fmt: str = "%Y-%m-%d",
        as_str: bool = False,
        year: Optional[Union[str | int]] = None,
    ) -> Union[List[Union[Tuple[date, ...], List[str]]], Sequence[Any]]:
        CUTOFFS_DIR = self.base_dir / "cutoffs"
        CUTOFFS_DIR.mkdir(parents=True, exist_ok=True)
        year = year or date.today().year

        file_path = (
            file_path or CUTOFFS_DIR / f"cutoffs_{year}.csv"
        )  # type: ignore
        with open(file_path, "r", newline="") as fd:
            cutoff_list: Sequence = list(csv.reader(fd))

        if as_str:
            return cutoff_list

        header, *rows = cutoff_list
        cutoffs = [header] + [to_date_object(row, date_fmt) for row in rows]
        return cutoffs

    def select_cutoff_period(
        self, deposit_date_idx: int, cutoffs=None
    ) -> Tuple[Union[str, date, None], Union[str, date]]:
        if cutoffs is None:
            cutoff_deposit_pairs = self.load_cutoffs()
            cutoff_deposit_pairs = self.load_cutoffs()[1:]
        else:
            cutoff_deposit_pairs = cutoffs

        deposit_date_idx = max(deposit_date_idx - 1, 0)

        if deposit_date_idx == 0:
            cutoff_date = cutoff_deposit_pairs[0][0]
            previous_cutoff_date = None
            try:
                previous_year = cutoff_date.year - 1
                previous_year_cutoffs = self.load_cutoffs(year=previous_year)[
                    1:
                ]
                if previous_year_cutoffs is not None:
                    previous_cutoff_date = previous_year_cutoffs[-1][0]
            except Exception:
                pass
        else:
            cutoff_date = cutoff_deposit_pairs[deposit_date_idx][0]
            previous_cutoff_date = cutoff_deposit_pairs[deposit_date_idx - 1][
                0
            ]

        return previous_cutoff_date, cutoff_date

    def purge_job_files(
        self,
        jobs: List[dict[str, Any]],
    ):
        for job in jobs:
            job_path = Path(job.job_path)
            if job_path.exists():
                purge_path = (
                    job_path if job_path.is_dir() else job_path.parent
                )
                unwanted_files = list(
                    purge_path.glob("**/*[mwzM][p4aiP][3avp3]")
                )
                for p in unwanted_files:
                    try:
                        p.unlink(missing_ok=True)
                    except OSError as e:
                        print(
                            f"Error deleting file {p}: {e}"
                        )  # Handle potential errors during unlinking


# if __name__ == "__main__":
# trans5 = Transcriptor()
# print(trans5.generate_summary_invoice(client_id=1))
