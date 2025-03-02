from platformdirs import user_config_dir, user_data_dir
import shutil
import zipfile
from pathlib import Path
from transcriptor.models import ConfigModel, ProfileModel
from transcriptor.api import API
from transcriptor.utils import sc, TEMPLATE_MAPPING, get_media_files, round_up
from transcriptor.utils import str_to_date as std, next_non_existent_file

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

        self.PROFILE_FILE = self.base_dir / "profile.yaml"
        if not self.PROFILE_FILE.exists() or self.PROFILE_FILE.stat().st_size == 0:
            self.profile = ProfileModel()
            self.profile.write(self.PROFILE_FILE)
        else:
            self.profile = ProfileModel.from_yaml(self.PROFILE_FILE)

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
        job_info = job_callback(job_file)
        client = self.api.get_clients({"id", job_info["client_id"]})
        if not client:
            print("No client found")
            return
        job_dir = self.create_job_dir(
            client.name,
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
                client.name, task_info["job_template"]
            )
            task_template_suffix = task_template_path.suffix

            task_file_path = next_non_existent_file(
                job_dir
                / f'{job_info["job_number"]} Due {job_info["date_due"].strftime("%m.%d")}{task_template_suffix}'
            )
            shutil.copy(task_template_path, task_file_path)

            task_rate_obj = self.api.get_rates(conditions={"client_id": client.id})
            task_info["job_rate"] = getattr(task_rate_obj, task_info["job_type"])
            task_info["amount"] = round_up(
                float(task_info["job_rate"]) * float(task_info["quantity"])
            )

            task_dict = {
                "client_id": client.id,
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


if __name__ == "__main__":
    trans5 = Transcriptor()
    print(trans5.config)
