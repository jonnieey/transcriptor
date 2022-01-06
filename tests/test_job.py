import pytest
from datetime import datetime, timedelta
from transcriptor.job import Job
from transcriptor.methods import create_job

DATE_STR_FMT = "%Y-%m-%d"
TODAY = datetime.today().strftime(DATE_STR_FMT)

@pytest.fixture()
def test_job():
    job = Job(
        date_received = datetime.today().strftime('%Y-%m-%d'),
        job_number = '56321',
        job_type = 'Normal',
        total_quantity = 40
    )
    return job

def test_job_to_dict(test_job):
    test_job.quantity = 20
    test_job.date_submitted = ''
    date_due = datetime.today() + timedelta(days=5)
    job_dict = {
        'date_received': datetime.today().strftime(DATE_STR_FMT),
        'job_number': '56321',
        'job_type':'Normal',
        'rate': 0.4,
        'total_quantity': 40,
        'quantity': 20,
        'date_due': date_due.strftime(DATE_STR_FMT),
        'date_submitted': '',
        'status': 'Pending',
    }

    assert test_job.to_dict() == job_dict

