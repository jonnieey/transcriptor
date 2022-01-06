from transcriptor.job import Job
from datetime import datetime, timedelta

DATE_STR_FMT = "%Y-%m-%d"

def test_job_to_dict():
    job = Job(
        date_received = datetime.today().strftime('%Y-%m-%d'),
        job_number = '56321',
        type = 'Normal',
        total_quantity = 40
    )
    job.quantity = 20
    job.date_submitted = ''

    date_due = datetime.today() + timedelta(days=5)
    job_dict = {
        'date_received': datetime.today().strftime(DATE_STR_FMT),
        'job_number': '56321',
        'type':'Normal',
        'rate': 0.4,
        'total_quantity': 40,
        'quantity': 20,
        'date_due': date_due.strftime(DATE_STR_FMT),
        'date_submitted': '',
        'status': 'Pending',
    }

    assert job.to_dict() == job_dict

