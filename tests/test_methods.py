import io
import json
import shutil
from datetime import date, datetime, timedelta

import pytest

from transcriptor.client import Client
from transcriptor.job import Job
from transcriptor.methods import (
    create_client,
    create_task,
    get_all_clients,
    get_date_due,
    get_date_received,
    save_client_job_to_file,
    save_client_to_file,
)
from transcriptor.utils import get_settings

settings = get_settings()
DATE_FMT, CLIENTS_FOLDER, JOBS_FOLDER, WORKS_FOLDER = (
    settings["date_fmt"],
    settings["clients_folder"],
    settings["jobs_folder"],
    settings["works_folder"],
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
    @classmethod
    def setup_class(cls):
        shutil.rmtree(CLIENTS_FOLDER.parent, ignore_errors=True)

    def test_create_client(
        self,
    ):
        client = create_client(name=CLIENT_NAME, email=CLIENT_EMAIL)
        assert isinstance(client, Client) is True
        assert client.name == CLIENT_NAME

    def test_save_client_to_file(self, test_client):
        save_client_to_file(test_client, CLIENTS_FOLDER)
        with open(CLIENTS_FOLDER / test_client.name, "r") as fp:
            client_json = json.load(fp)
        assert client_json["name"] == test_client.name

    def test_create_task(
        self,
    ):
        job = create_task(
            date_received=TODAY,
            job_number="511113",
            job_type="Normal",
            quantity=80,
            total_quantity=180,
            date_due=TODAY + timedelta(days=5),
            job_path=WORKS_FOLDER / "TestDir",
        )
        assert isinstance(job, Job)

    def test_save_client_job_to_file(self, test_client, test_job):
        save_client_job_to_file(test_client, [test_job], JOBS_FOLDER)
        with open(JOBS_FOLDER / test_client.name, "r") as fp:
            client_jobs_json = json.load(fp)

        assert client_jobs_json["client"] == test_client.to_dict()
        assert client_jobs_json["jobs_list"] == [test_job.to_dict()]

    def test_get_date_received_as_date_string(
        self,
    ):
        date_received = "2021-11-12"
        date_rec = get_date_received(date_received)
        print(date_rec)
        assert date_rec == datetime.strptime(date_received, DATE_FMT).date()

    def test_get_date_received_as_int(
        self,
    ):
        date_received = -2
        date_rec = get_date_received(date_received)
        assert date_rec == TODAY + timedelta(days=date_received)

    def test_get_date_due_as_date_string(
        self,
    ):
        date_due = "2021-11-15"
        date_d = get_date_due(date_due)
        assert date_d == datetime.strptime(date_due, DATE_FMT).date()

    def test_get_date_due_as_int(
        self,
    ):
        date_due = -2  # Convert to abs
        date_d = get_date_due(date_due)
        assert date_d == TODAY + timedelta(days=abs(date_due))

    def test_get_all_clients(self, test_client):
        save_client_to_file(test_client, CLIENTS_FOLDER)
        client2 = Client("TestClient1", "TestEmail1")
        save_client_to_file(client2, CLIENTS_FOLDER)

        clients = get_all_clients(CLIENTS_FOLDER)

        assert len(clients) == 2
