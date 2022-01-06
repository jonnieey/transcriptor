from datetime import timedelta, datetime
import json
from transcriptor.client import Client

class Job:
    def __init__(
        self,
        date_received: str,
        job_number: str,
        job_type : str,
        total_quantity : float,
        quantity : float= 0.0,
        date_due: str = '',
        date_submitted: str = '' ,
        status: str = 'Pending',
    ) -> None:
        self.date_received = date_received
        self.job_number = job_number
        self.job_type = job_type
        self.rate = self.get_job_details(job_type)['rate']
        self.total_quantity = total_quantity
        self.quantity = quantity
        self.date_due = date_due if date_due != '' else self.get_date_due(job_type)
        self.date_submitted = date_submitted
        self.status = status

    @property
    def job_type(self) -> str:
        return self._job_type

    @job_type.setter
    def job_type(self, value):
        self._job_type = value
        self._rate = self.get_job_details(value)['rate']
        self._date_due = self.get_date_due(value)

    @property
    def job_number(self) -> str:
        return self._job_number

    @job_number.setter
    def job_number(self, value):
        self._job_number = value

    @property
    def rate(self) -> float:
        return self._rate

    @rate.setter
    def rate(self, value):
        self._rate = value

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

    def get_job_details(self, job_type):
        job_types = {
            'Expedite' : {'rate': 0.60, 'due_in': 1},
            'Normal': {'rate': 0.40, 'due_in': 5 },
            'Interpreted': {'rate':0.30,'due_in': 5},
        } # Use a file
        return job_types[job_type]

    def get_date_due(self, job_type: str ):
        due_date = (datetime.today() + timedelta(abs(self.get_job_details(job_type)['due_in']))).strftime("%Y-%m-%d")
        return due_date

    def __str__(self):
        j = "%s %s %s %s %s %s" % (
            self.job_number,
            self.date_received,
            self.job_type,
            self.quantity,
            self.rate,
            self.date_due,
        )
        return j

    def to_dict(self):
        d = {}

        d['date_received'] = self._date_received
        d['job_number'] = self._job_number
        d['job_type'] = self._job_type
        d['rate'] = self._rate
        d['total_quantity'] = self._total_quantity
        d['quantity'] = self._quantity
        d['date_due'] = self._date_due
        d['date_submitted'] = self._date_submitted
        d['status'] = self._status

        return d

    def to_json(self, indent=2, ensure_ascii=False):
        return json.dumps(
            self.to_dict(),
            indent=indent,
            ensure_ascii=ensure_ascii,
            sort_keys=True,
        )
