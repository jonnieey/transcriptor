import pytest
from datetime import datetime, timedelta, date

from transcriptor.job import Job
from transcriptor.methods import create_job
from transcriptor.client import Client
from transcriptor.methods import create_client, get_job_details_from_zip, get_date_received

CLIENT_NAME = 'TestClient'
CLIENT_EMAIL = 'TestEmail'

DATE_FMT = "%Y-%m-%d"
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

def test_create_client():
    client = create_client(name=CLIENT_NAME, email=CLIENT_EMAIL)
    assert isinstance(client, Client) is True
    assert client.name == CLIENT_NAME

def test_save_client_to_file(test_client):
    pass

def test_create_job():
    job = create_job(
        date_received=TODAY,
        job_number='511113',
        job_type='Normal',
        total_quantity=180,
        date_due=(TODAY + timedelta(days=5)).strftime('%Y-%m-%d'),
    )
    assert isinstance(job, Job)

def test_save_job_to_file(test_job):
    pass

def test_save_client_job_to_file(test_job):
    pass

def test_get_job_details_from_zip():
    zip = "2021-11-12-514779_DUE_11.15_(EXAMPLE)/514779 DUE 11.15 (EXAMPLE).zip"

    job_number, date_due = get_job_details_from_zip(zip)
    assert job_number == '514779'

    d = '%s-11-15' % (TODAY.year)
    assert datetime.strptime(date_due, DATE_FMT).date() ==  datetime.strptime(d, DATE_FMT).date()

def test_get_date_received_as_date_string():
    date_received = '2021-11-12'
    date_rec = get_date_received(date_received)
    assert date_rec == datetime.strptime(date_received, '%Y-%m-%d')

def test_get_date_received_as_int():
    date_received = -2
    date_rec = get_date_received(date_received)
    assert date_rec == TODAY + timedelta(days=date_received)
