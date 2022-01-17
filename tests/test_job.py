from datetime import date, timedelta
from pathlib import Path

import pytest

from transcriptor.job import Job
from transcriptor.utils import date_to_string

DATE_FMT = "%Y-%m-%d"
TODAY = date.today()


@pytest.fixture()
def test_job():
    job = Job(
        date_received=TODAY,
        job_number="56321",
        job_type="Normal",
        total_quantity=40,
        job_rate=0.4,
        job_path=Path("somerandompath"),
    )
    return job


def test_job_to_dict(test_job):
    test_job.quantity = 20
    date_due = date.today() + timedelta(days=5)
    job_dict = {
        "date_received": date_to_string(TODAY),
        "job_number": "56321",
        "job_type": "Normal",
        "job_rate": 0.4,
        "total_quantity": 40,
        "quantity": 20,
        "date_due": date_to_string(date_due),
        "date_submitted": "",
        "status": "Pending",
        "amount": 0.0,
        "amount_paid": 0.0,
        "job_path": "somerandompath",
    }

    assert test_job.to_dict() == job_dict


def test_job_from_json():
    date_due = date.today() + timedelta(days=5)
    job_dict = {
        "date_received": date_to_string(TODAY),
        "job_number": "56321",
        "job_type": "Normal",
        "job_rate": 0.4,
        "total_quantity": 40,
        "quantity": 20,
        "date_due": date_to_string(date_due),
        "date_submitted": "",
        "status": "Pending",
        "amount": 0.0,
        "amount_paid": 0.0,
        "job_path": "somerandompath",
    }
    job = Job.from_json(job_dict)
    assert job.job_number == job_dict["job_number"]


def test_amount_paid_less_than_amount():
    date_due = date.today() + timedelta(days=5)
    job_dict = {
        "date_received": date_to_string(TODAY),
        "job_number": "56321",
        "job_type": "Normal",
        "job_rate": 0.4,
        "total_quantity": 40,
        "quantity": 20,
        "date_due": date_to_string(date_due),
        "date_submitted": "",
        "status": "Pending",
        "amount": 400,
        "amount_paid": 500,
        "job_path": "somerandompath",
    }
    job = Job.from_json(job_dict)
    print(job.amount_paid)
    assert job.amount_paid == 400
