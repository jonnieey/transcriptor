from platformdirs import user_config_dir, user_data_dir
import shutil
import zipfile
from pathlib import Path
from transcriptor.models import ConfigModel
from transcriptor.api import API
from transcriptor.utils import sc, TEMPLATE_MAPPING
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
                self.config = ConfigModel(**DEFAULT_CONFIG)
                self.config.write(self.CONFIG_FILE)
            else:
                self.config = ConfigModel.from_yaml(self.CONFIG_FILE)
        else:
            self.config = config

        self.base_dir = Path(self.config.base_dir)
        self.date_format = self.config.date_format
        self.api = api if api is not None else API(base_dir=self.base_dir)

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
        job_num: str,
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
            / f"{date_received.strftime('%d_%a')}_{job_num}_DUE_{date_due.strftime('%d_%a')}"
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
            shutil.move(job_file, job_dir)

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


if __name__ == "__main__":
    trans5 = Transcriptor()
    print(trans5.config)
