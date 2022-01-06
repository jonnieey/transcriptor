import pytest

from datetime import datetime
from transcriptor.job import Job
from transcriptor.methods import create_job
from transcriptor.client import Client
from transcriptor.methods import create_client

CLIENT_NAME = 'TestClient'
CLIENT_EMAIL = 'TestEmail'

DATE_STR_FMT = "%Y-%m-%d"
TODAY = datetime.today().strftime(DATE_STR_FMT)

@pytest.fixture()
def test_client():
    return Client(name=CLIENT_NAME, email=CLIENT_EMAIL)

@pytest.fixture()
def test_job():
    job = Job(
        date_received = datetime.today().strftime('%Y-%m-%d'),
        job_number = '56321',
        job_type = 'Normal',
        total_quantity = 40
    )
    return job

def test_create_client():
    client = create_client(name=CLIENT_NAME, email=CLIENT_EMAIL)
    assert isinstance(client, Client) is True
    assert client.name == CLIENT_NAME

def test_save_client_to_file(test_client):
    pass

def test_create_job():
    job = create_job(date_received=TODAY, job_number='511113', job_type='Normal', total_quantity=180)
    assert isinstance(job, Job)

def test_save_job_to_file(test_job):
    pass

def test_save_client_job_to_file(test_job):
    pass
