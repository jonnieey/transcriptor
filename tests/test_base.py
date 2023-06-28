import shutil
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

from transcriptor.api import API
from transcriptor.base import Transcriptor
from transcriptor.models import ConfigModel, ProfileModel

today = date.today()


class TestTranscriptor(unittest.TestCase):
    def setup_class(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.api = API(self.temp_dir)
        self.app = Transcriptor(api=self.api)

    def teardown_class(self):
        shutil.rmtree(self.temp_dir)

    def test_load_config(self):
        config = self.app.load_config()
        self.assertIsInstance(config, ConfigModel)

    def test_load_profile(self):
        profile = self.app.load_profile()
        self.assertIsInstance(profile, ProfileModel)

    def test_create_client(self):
        self.app.create_client("test_name", "test_email")
        self.assertTrue(self.temp_dir.joinpath("clients", "test_name").exists())

    def test_create_job(self):
        self.app.create_client("testclient", "testclientemail")
        media_file = Path(__file__).parent.joinpath(
            "media_files", "488460 BACKUP - 22 MINS.m4a"
        )
        date_rec = datetime.strptime("2020-01-05", "%Y-%m-%d").date()
        date_due = datetime.strptime("2020-01-10", "%Y-%m-%d").date()
        job_num = "488460"
        job_cb = lambda job_file: {
            "client_id": 1,
            "date_rec": date_rec,
            "date_due": date_due,
            "job_num": job_num,
        }
        task_cb = lambda task: {
            "date_rec": date_rec,
            "date_due": date_due,
            "status": "Pending",
            "amount": 50.0,
            "amount_paid": 0.0,
            "total_quantity": 1000.0,
            "quantity": 500.0,
            "job_type": "Normal",
            "job_rate": 0.50,
            "job_template": "zd",
            "job_path": "/path/to/job1",
            "note": "test notes",
        }
        self.app.create_job(media_file, job_cb, task_cb)
        jobs = self.api.get_jobs()
        self.assertEqual(len(jobs), 1)
        self.assertTrue(
            self.temp_dir.joinpath("clients", "test_name", "templates").exists()
        )

        self.assertTrue(
            self.temp_dir.joinpath(
                "clients",
                "test_name",
                f"{date_rec.year}",
                f"{date_rec.strftime('%B')}",
                f"{date_rec.strftime('%d_%a')}_{job_num}_DUE_{date_due.strftime('%d_%a')}",
            ).exists()
        )
