from datetime import timedelta, date, datetime
import json
from transcriptor.utils import date_to_string, string_to_date

DATE_FORMAT = '%Y-%m-%d'
class Job:
    def __init__(
        self,
        date_received: date,
        job_number: str,
        job_type : str,
        total_quantity : float,
        job_rate : float = None,
        quantity : float= 0.0,
        date_due: date = None,
        date_submitted: date = None ,
        status: str = 'Pending',
    ) -> None:
        self.date_received = date_received
        self.job_number = job_number
        self.job_type = job_type
        self.total_quantity = total_quantity
        self.quantity = quantity
        self.date_submitted = date_submitted
        self.status = status
        self.job_rate = job_rate
        self.date_due =  date_due

        if date_due is None and job_type:
            date_due = self.get_date_due(date_received, job_type)
            self.date_due =  date_due

        elif isinstance(date_due, str):
            date_due = string_to_date(date_due)
            self.date_due = date_due

        if job_rate is None and job_type:
            job_rate = self.get_job_rate(job_type)
            self.job_rate = job_rate

    @property
    def job_type(self) -> str:
        return self._job_type

    @job_type.setter
    def job_type(self, value):
        self._job_type = value

    @property
    def job_number(self) -> str:
        return self._job_number

    @job_number.setter
    def job_number(self, value):
        self._job_number = value

    @property
    def job_rate(self) -> float:
        return self._job_rate

    @job_rate.setter
    def job_rate(self, value):
        self._job_rate = value

    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(self, value):
        self._quantity = value

    @property
    def total_quantity(self):
        return self._total_quantity

    @total_quantity.setter
    def total_quantity(self, value):
        self._total_quantity = value

    @property
    def date_received(self):
        return self._date_received

    @date_received.setter
    def date_received(self, value):
        self._date_received = value

    @property
    def date_due(self):
        return self._date_due

    @date_due.setter
    def date_due(self, value):
        self._date_due = value

    @property
    def date_submitted(self):
        return self._date_submitted

    @date_submitted.setter
    def date_submitted(self, value):
        self._date_submitted = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    def __str__(self):
        j = "%s %s %s %s %s %s" % (
            self.job_number,
            self.date_received,
            self.job_type,
            self.quantity,
            self.job_rate,
            self.date_due,
        )
        return j

    def get_date_due(self, date_received, job_type):
        job_types = {'Normal': 5, 'Interpreted': 5, 'Expedite': 1}
        job_days = job_types[job_type]
        due_date = datetime.strptime(date_received.strftime(DATE_FORMAT), DATE_FORMAT) + timedelta(days=job_days)
        return due_date.date()

    def get_job_rate(self, job_type):
        job_types = {'Normal': 0.4, 'Interpreted': 0.3, 'Expedite': 0.6}
        return job_types[job_type]

    def to_dict(self):
        d = {}

        d['date_received'] = date_to_string(self._date_received)
        d['job_number'] = self._job_number
        d['job_type'] = self._job_type
        d['job_rate'] = self._job_rate
        d['total_quantity'] = self._total_quantity
        d['quantity'] = self._quantity
        d['date_due'] = date_to_string(self._date_due)
        d['date_submitted'] = date_to_string(self._date_submitted)
        d['status'] = self._status

        return d

    def to_json(self, indent=2, ensure_ascii=False):
        return json.dumps(
            self.to_dict(),
            indent=indent,
            ensure_ascii=ensure_ascii,
            sort_keys=True,
        )
