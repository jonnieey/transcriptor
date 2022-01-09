import pytest
from pathlib import Path
from datetime import timedelta, date
from transcriptor.job import Job
from transcriptor.utils import date_to_string

DATE_FMT = "%Y-%m-%d"
TODAY = date.today()

@pytest.fixture()
def test_job():
    job = Job(
        date_received = TODAY,
        job_number = '56321',
        job_type = 'Normal',
        total_quantity = 40,
        job_rate = 0.4,
        job_path = Path('somerandompath'),
    )
    return job

def test_job_to_dict(test_job):
    test_job.quantity = 20
    date_due = date.today() + timedelta(days=5)
    job_dict = {
        'date_received': date_to_string(TODAY),
        'job_number': '56321',
        'job_type':'Normal',
        'job_rate': 0.4,
        'total_quantity': 40,
        'quantity': 20,
        'date_due': date_to_string(date_due),
        'date_submitted': None,
        'status': 'Pending',
        'amount_paid': 0.0,
        'job_path' : 'somerandompath',
    }

    assert test_job.to_dict() == job_dict

