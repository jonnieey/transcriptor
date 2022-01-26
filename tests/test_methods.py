import copy
import json
import shutil
from datetime import date, datetime, timedelta

import pytest

from transcriptor.client import Client
from transcriptor.conf import get_config
from transcriptor.job import Job
from transcriptor.methods import *

settings = Settings(**get_config())


DATE_FMT, CLIENTS_FOLDER, JOBS_FOLDER, WORKS_FOLDER = (
    settings.date_fmt,
    settings.clients_folder,
    settings.jobs_folder,
    settings.works_folder,
)

CLIENT_NAME = "TestClient"
CLIENT_EMAIL = "TestEmail"

TODAY = date.today()


@pytest.fixture()
def test_client():
    return Client(name=CLIENT_NAME, email=CLIENT_EMAIL)


@pytest.fixture()
def test_job():
    job = Job(
        date_received=TODAY,
        job_number="56321",
        job_type="Normal",
        total_quantity=40,
        job_path=WORKS_FOLDER / "2000-12-12-404404_DUE_2000-12-17",
    )
    return job


class Tests:
    def teardown_method(self):
        shutil.rmtree(CLIENTS_FOLDER.parent, ignore_errors=True)

    def test_create_client(self):
        client = create_client(name=CLIENT_NAME, email=CLIENT_EMAIL)
        assert isinstance(client, Client) is True
        assert client.name == CLIENT_NAME

    def test_save_client_to_file(self, test_client):
        save_client(test_client, CLIENTS_FOLDER)
        with open(CLIENTS_FOLDER / test_client.name, "r") as fp:
            client_json = json.load(fp)
        assert client_json["name"] == test_client.name

    def test_create_task(self):
        job = create_task(
            date_received=TODAY,
            job_number="511113",
            job_type="Normal",
            quantity=80,
            total_quantity=180,
            date_due=TODAY + timedelta(days=5),
            job_path=WORKS_FOLDER / "TestDir",
            note="",
        )
        assert isinstance(job, Job)

    def test_save_client_job_to_file(self, test_client, test_job):
        save_job_to_file(test_client, [test_job], JOBS_FOLDER)
        with open(JOBS_FOLDER / test_client.name, "r") as fp:
            client_jobs_json = json.load(fp)

        assert client_jobs_json["client"] == test_client.to_dict()
        assert client_jobs_json["jobs_list"] == [test_job.to_dict()]

    def test_get_date_received_as_date_string(self):
        date_received = "2021-11-12"
        date_rec = get_date_received(date_received)
        assert date_rec == datetime.strptime(date_received, DATE_FMT).date()

    def test_get_date_received_as_positive_int(self):
        date_received_positive = 2
        date_rec_positive = get_date_received(date_received_positive)
        assert date_rec_positive == TODAY + timedelta(days=-abs(date_received_positive))

    def test_get_date_received_as_negative_int(self):
        date_received_negative = -2
        date_rec_negative = get_date_received(date_received_negative)
        assert date_rec_negative == TODAY + timedelta(days=date_received_negative)

    def test_get_date_due_as_date_string(self):
        date_due = "2021-11-15"
        date_d = get_date_due(date_due)
        assert date_d == datetime.strptime(date_due, DATE_FMT).date()

    def test_get_date_due_as_int(self):
        date_due = -2  # Convert to abs
        date_d = get_date_due(date_due)
        assert date_d == TODAY + timedelta(days=date_due)

    def test_get_all_clients(self, test_client):
        save_client(test_client, CLIENTS_FOLDER)
        client2 = Client("TestClient1", "TestEmail1")
        save_client(client2, CLIENTS_FOLDER)

        clients = get_clients(CLIENTS_FOLDER)

        assert len(clients) == 2

    def test_get_jobs_with_client(self, test_client, test_job):
        save_job_to_file(test_client, [test_job, test_job])
        jobs = get_jobs(test_client.name)
        assert len(jobs.jobs()) == 2

    def test_get_jobs_without_client(self, test_client, test_job):
        save_job_to_file(test_client, [test_job, test_job])
        client2 = Client(name="TestClient2", email="TestEmail2")
        save_job_to_file(client2, [test_job, test_job])
        jobs = get_jobs()

        assert len(jobs.jobs()) == 4

    def test_update_job(self, test_client, test_job):
        save_job_to_file(test_client, [test_job])
        update_dict = {
            "quantity": 20,
            "amount_paid": 10.0,
            "status": "Done",
            "date_submitted": TODAY.strftime(DATE_FMT),
        }
        update_job(test_job.job_number, update_dict)
        with open(JOBS_FOLDER / test_client.name, "r") as fp:
            client_jobs_json = json.load(fp)

        # TODO add method to get job from job list
        assert client_jobs_json["jobs_list"][0]["amount"] == 8.0
        assert client_jobs_json["jobs_list"][0]["amount_paid"] == 8.0
        assert client_jobs_json["jobs_list"][0]["status"] == "Done"
        assert client_jobs_json["jobs_list"][0]["date_submitted"] == TODAY.strftime(
            DATE_FMT
        )

    def test_filter_jobs_by_date(self, test_job):
        job1 = copy.copy(test_job)
        job1.date_received = TODAY - timedelta(days=20)
        job1.date_due = TODAY - timedelta(days=15)
        job1.date_submitted = TODAY - timedelta(days=14)

        job2 = copy.copy(test_job)
        job2.date_received = TODAY - timedelta(days=10)
        job2.date_due = TODAY - timedelta(days=5)
        job2.date_submitted = TODAY - timedelta(days=6)

        job3 = copy.copy(test_job)
        job3.date_received = TODAY - timedelta(days=4)
        job3.date_due = TODAY - timedelta(days=3)
        job3.date_submitted = TODAY - timedelta(days=3)

        jobs = [job for job in (job1, job2, job3)]

        ten_days = TODAY - timedelta(days=10)
        three_days = TODAY - timedelta(days=3)
        thirty_days = TODAY - timedelta(days=30)

        less_than_three_days = filter_jobs_by_date(
            "date_received", three_days, TODAY, jobs
        )
        less_than_ten_days = filter_jobs_by_date("date_due", ten_days, TODAY, jobs)
        more_than_ten_days = filter_jobs_by_date(
            "date_submitted", thirty_days, ten_days, jobs
        )

        assert len(less_than_three_days) == 0
        assert len(less_than_ten_days) == 2
        assert len(more_than_ten_days) == 1
