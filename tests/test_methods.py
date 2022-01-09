import io
import json
import pytest
import shutil

from datetime import datetime, timedelta, date
from pathlib import Path

from transcriptor.client import Client
from transcriptor.job import Job

from transcriptor.methods import (
    create_client,
    create_task,
    get_date_received,
    get_date_due,
    get_job_details_from_zip,
    save_client_to_file,
    save_client_job_to_file,
    get_all_clients
)
from transcriptor.utils import SETTINGS

DATE_FMT, CLIENTS_FOLDER, JOBS_FOLDER = (
    SETTINGS['date_fmt'],
    SETTINGS['clients_folder'],
    SETTINGS['jobs_folder'],
)

CLIENT_NAME = 'TestClient'
CLIENT_EMAIL = 'TestEmail'

TODAY = date.today()

@pytest.fixture()
def test_client():
    return Client(name=CLIENT_NAME, email=CLIENT_EMAIL)

@pytest.fixture()
def test_job():
    job = Job(
        date_received = TODAY,
        job_number = '56321',
        job_type = 'Normal',
        total_quantity = 40
    )
    return job

class Tests:
    @classmethod
    def setup_class(cls):
        shutil.rmtree(CLIENTS_FOLDER.parent, ignore_errors=True)

    def test_create_client(self,):
        client = create_client(name=CLIENT_NAME, email=CLIENT_EMAIL)
        assert isinstance(client, Client) is True
        assert client.name == CLIENT_NAME

    def test_save_client_to_file(self,test_client):
        save_client_to_file(test_client, CLIENTS_FOLDER)
        with open(CLIENTS_FOLDER / test_client.name, 'r') as fp:
            client_json = json.load(fp)
        assert client_json['name'] == test_client.name

    def test_create_task(self,):
        job = create_task(
            date_received=TODAY,
            job_number='511113',
            job_type='Normal',
            quantity=80,
            total_quantity=180,
            date_due=(TODAY + timedelta(days=5)).strftime(DATE_FMT),
        )
        assert isinstance(job, Job)

    def test_save_client_job_to_file(self, test_client, test_job):
        save_client_job_to_file(test_client, [test_job], JOBS_FOLDER)
        with open(JOBS_FOLDER / test_client.name, 'r') as fp:
            client_jobs_json = json.load(fp)

        assert client_jobs_json['client'] == test_client.to_dict()
        assert client_jobs_json['job_list'] == [test_job.to_dict()]

    def test_get_job_details_from_zip(self,):
        zip = "2021-11-12-514779_DUE_11.15_(EXAMPLE)/514779 DUE 11.15 (EXAMPLE).zip"
        job_number, date_due = get_job_details_from_zip(zip)
        assert job_number == '514779'
        d = '%s-11-15' % (TODAY.year)
        assert date_due ==  d

    def test_get_date_received_as_date_string(self,):
        date_received = '2021-11-12'
        date_rec = get_date_received(date_received)
        print(date_rec)
        assert date_rec == datetime.strptime(date_received, DATE_FMT).date()

    def test_get_date_received_as_int(self,):
        date_received = -2
        date_rec = get_date_received(date_received)
        assert date_rec == TODAY + timedelta(days=date_received)

    def test_get_date_due_as_date_string(self,):
        date_due = '2021-11-15'
        date_d = get_date_due(date_due)
        assert date_d == datetime.strptime(date_due, DATE_FMT).date()

    def test_get_date_due_as_int(self,):
        date_due = -2 # Convert to abs
        date_d = get_date_due(date_due)
        assert date_d == TODAY + timedelta(days=abs(date_due))

    def test_get_all_clients(self,test_client):
        save_client_to_file(test_client, CLIENTS_FOLDER)
        client2 = Client('TestClient1', 'TestEmail1')
        save_client_to_file(client2, CLIENTS_FOLDER)

        clients = get_all_clients(CLIENTS_FOLDER)

        assert len(clients) == 2
