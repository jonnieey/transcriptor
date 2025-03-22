from platformdirs import user_config_dir, user_data_dir
import csv
import shutil
from pprint import pprint
import zipfile
from datetime import date, datetime
from pathlib import Path
from transcriptor.models import (
    Config,
    Profile,
    InvoiceLine,
    Invoice,
    SummaryInvoiceLine,
    SummaryInvoice,
)
from transcriptor.api import API
from transcriptor.utils import (
    sc,
    TEMPLATE_MAPPING,
    get_media_files,
    round_up,
    to_date_object,
    extract_table_data_from_docx,
    next_non_existent_file,
    render_invoice,
    render_summary_invoice,
    html_to_md,
    htmlstr_to_pdf,
)
from transcriptor.utils import str_to_date as std

APP_NAME = "transcriptor5"
CONFIG_FILE_NAME = "config5.yaml"

DEFAULT_CONFIG = {
    "base_dir": f"{user_data_dir(APP_NAME)}",
    "date_format": "%Y-%m-%d",
}


class Transcriptor:
    CONFIG_DIR = Path(user_config_dir(APP_NAME))
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True)
    CONFIG_FILE = CONFIG_DIR / CONFIG_FILE_NAME

    def __init__(self, api=None, config=None):
        if config is None:
            if not self.CONFIG_FILE.exists() or self.CONFIG_FILE.stat().st_size == 0:
                self.config = Config(**DEFAULT_CONFIG)
                self.config.write(self.CONFIG_FILE)
            else:
                self.config = Config.from_yaml(self.CONFIG_FILE)
        else:
            self.config = config

        self.base_dir = Path(self.config.base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.date_format = self.config.date_format

        self.PROFILE_FILE = self.base_dir / "profile.yaml"
        if not self.PROFILE_FILE.exists() or self.PROFILE_FILE.stat().st_size == 0:
            self.profile = Profile()
            self.profile.write(self.PROFILE_FILE)
        else:
            self.profile = Profile.from_yaml(self.PROFILE_FILE)

        self.api = api if api is not None else API(base_dir=self.base_dir)

    def save_config(self):
        self.config.write(self.CONFIG_FILE)

    def save_profile(self):
        self.profile.write(self.PROFILE_FILE)

    def create_client(self, name, email, rates_dict: dict = None):
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
        date_received = std(date_received, self.date_format)
        date_due = std(date_due, self.date_format)

        job_dir = (
            self.base_dir
            / "clients"
            / sc(client_name)
            / f"{date_received.year}"
            / f"{date_received.strftime('%B')}"
            / f"{date_received.strftime('%d_%a')}_{job_number}_DUE_{date_due.strftime('%d_%a')}"
        )
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir

    @staticmethod
    def mv_extract_job_file(job_file: Path, job_dir: Path) -> None:
        """
        Move/Extract job file to jobs directory

        Arguments:
            job_file: Path object or path-like string to job file
            job_dir: Path object or path-like string to job directory
        """
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
        client_template_dir = self.base_dir / "clients" / sc(client) / "templates"

        if not client_template_dir.exists():
            jobs_templates_path = Path(__file__).parent / "templates"
            shutil.copytree(
                jobs_templates_path, client_template_dir, dirs_exist_ok=True
            )

        return client_template_dir / TEMPLATE_MAPPING[template]

    def create_job(self, job_file, job_callback, task_callback):
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
            task_info["job_rate"] = task_rate_obj[0].get(task_info["job_type"].lower())
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

    def delete_clients(self, conditions=None, raw_sql_stmt=None, purge=False):
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
        jobs = self.api.delete_jobs(conditions=conditions, raw_sql_stmt=raw_sql_stmt)
        if purge:
            for job in jobs:
                job_path = Path(job["job_path"])
                shutil.rmtree(job_path.parent)
        return jobs

    def read_invoice_counter(self, invoice_num_counter_file):
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

    def generate_invoice(self, client_id, conditions=None, raw_sql_stmt=None):
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
                raw_sql_stmt = (
                    f"{raw_sql_stmt} AND client_id = {client_id} AND amount_paid = 0"
                )
            else:
                raw_sql_stmt = f"{raw_sql_stmt} AND amount_paid = 0"

        jobs = self.api.get_jobs(conditions=conditions, raw_sql_stmt=raw_sql_stmt)
        if not jobs:
            print("No jobs found")
            return ("", "")

        invoice_lines = [InvoiceLine.parse_obj(job) for job in jobs]
        client = jobs[0].get("client")
        client_name = client.name if hasattr(client, "name") else client

        INVOICE_DIR = self.base_dir / "clients" / sc(client_name) / "invoices"
        INVOICE_NUM_COUNTER_FILE = INVOICE_DIR / "invoice_number_counter"

        invoice_number = self.read_invoice_counter(INVOICE_NUM_COUNTER_FILE)

        invoice = Invoice(
            profile=self.profile,
            invoice_number=f"{invoice_number + 1:05}",
            client_name=client_name,
            jobs=invoice_lines,
        )
        html = render_invoice(invoice=invoice)

        return html, client_name

    def generate_summary_invoice(self, client_id, previous_year_cutoff=None):
        client_name = None
        cutoffs = self.load_cutoffs(as_str=True)

        if client_id is None:
            print("CLIENT ID CANNOT BE NONE")
            return ("", "")

        jobs_by_month = {str(i): [] for i in range(1, 13)}

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
                c for c in conditions["date_submitted"] if c
            ]

            jobs = self.api.get_jobs(conditions=conditions)
            if jobs:
                if client_name is None:
                    client = jobs[0].get("client")
                    client_name = client.name if hasattr(client, "name") else client
                month_idx = std(deposit_date, "%Y-%m-%d").month
                jobs_by_month[str(month_idx)].extend(jobs)

        months_summary_list = []
        for idx in range(1, 13):
            month = str(idx)
            jobs = jobs_by_month[month]

            month_info = {
                "month": date(year=datetime.now().year, month=idx, day=1).strftime(
                    "%B"
                ),
                "job_count": len(jobs),
                "total": round(sum(job["amount_paid"] for job in jobs), 2),
            }
            months_summary_list.append(SummaryInvoiceLine.parse_obj(month_info))

        summary_invoice = SummaryInvoice(
            profile=self.profile,
            client_name=client_name,
            summary_lines=months_summary_list,
        )
        html = render_summary_invoice(summary_invoice=summary_invoice)

        return html, client_name

    def html_to_pdf(self, html, client_name, output_file=None, summary_invoice=False):
        INVOICE_DIR = self.base_dir / "clients" / sc(client_name) / "invoices"

        if not INVOICE_DIR.exists():
            INVOICE_DIR.mkdir(parents=True, exist_ok=True)

        date_str = date.today().strftime("%Y-%m-%d")
        client_name_sc = sc(client_name)
        file_type = "summary" if summary_invoice else "invoice"

        INVOICE_FILE = INVOICE_DIR / f"{date_str}_{client_name_sc}_{file_type}.pdf"

        htmlstr_to_pdf(html, output_path=INVOICE_FILE)

        if summary_invoice is False:
            INVOICE_NUM_COUNTER_FILE = INVOICE_DIR / "invoice_number_counter"
            self.increase_invoice_counter(INVOICE_NUM_COUNTER_FILE)

    def to_md(self, html):
        return html_to_md(html)

    def generate_cutoff_list_from_docx(self, docx_path, date_fmt=None):
        date_fmt = date_fmt or "%m/%d/%Y"
        cutoff_list = extract_table_data_from_docx(docx_path)

        header, *rows = cutoff_list
        cutoffs = [header] + [to_date_object(row, date_fmt) for row in rows]
        return cutoffs

    def save_cutoffs(self, cutoffs, file_path=None):
        file_path = file_path or self.base_dir.joinpath("cutoffs.csv")
        with open(file_path, "w", newline="") as fd:
            writer = csv.writer(fd)
            writer.writerows(cutoffs)

    def load_cutoffs(self, file_path=None, date_fmt="%Y-%m-%d", as_str=False):
        file_path = file_path or self.base_dir.joinpath("cutoffs.csv")
        with open(file_path, "r", newline="") as fd:
            cutoff_list = list(csv.reader(fd))

        if as_str:
            return cutoff_list

        header, *rows = cutoff_list
        cutoffs = [header] + [to_date_object(row, date_fmt) for row in rows]
        return cutoffs

    def select_cutoff_period(self, deposit_date_idx):
        cutoff_deposit_pairs = self.load_cutoffs()

        cutoff_deposit_pairs = self.load_cutoffs()[1:]

        deposit_date_idx = max(deposit_date_idx - 1, 0)

        if deposit_date_idx == 0:
            cutoff_date = cutoff_deposit_pairs[0][0]
            previous_cutoff_date = None
        else:
            cutoff_date = cutoff_deposit_pairs[deposit_date_idx][0]
            previous_cutoff_date = cutoff_deposit_pairs[deposit_date_idx - 1][0]

        return previous_cutoff_date, cutoff_date


if __name__ == "__main__":
    trans5 = Transcriptor()
    print(trans5.generate_summary_invoice(client_id=1))
