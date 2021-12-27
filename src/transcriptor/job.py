from datetime import date, timedelta, datetime
from typing import Type, Optional

from client import Client

class Job:
    def __init__(
        self,
        client: Optional[Client],
        date_received: date,
        job_number: str,
        type : str,
        quantity : float=None,
        date_due: date=None,
        date_submitted: date=None,
    ) -> None:
        self.client = client
        self.date_received = date_received
        self.job_number = job_number
        self.type = type
        self.rate = self.get_job_details(type)['rate']
        self.quantity = quantity
        self.date_due = date_due if date_due is not None else datetime.today() + timedelta(abs(self.get_job_details(type)['due_in']))
        self.date_submitted = date_submitted

    @property
    def type(self) -> str:
        return self._type

    @type.setter
    def type(self, value):
        self._type = value

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
    def client(self) -> Client:
        return self._client

    @client.setter
    def client(self, value: Client):
        self._client = value

    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(self, value):
        self._quantity = value

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

    def get_job_details(self, job_type):
        job_types = {
            'Expedite' : {'rate': 0.60, 'due_in': 1},
            'Normal': {'rate': 0.40, 'due_in': 5 },
            'Interpreted': {'rate':0.30,'due_in': 5},
        } # Use a file
        return job_types[job_type]

    def __str__(self):
        j = "%s %s %s %s %s %s %s" % (self.client, self.job_number, self.date_received, self.type, self.quantity, self.rate, self.date_due)
        return j

    def to_dict(self):
        d = {}

        d['client'] = self._client
        d['date_received'] = self._date_received
        d['job_number'] = self._job_number
        d['type'] = self._type
        d['rate'] = self._rate
        d['quantity'] = self._quantity
        d['date_due'] = self._date_due
        d['date_submitted'] = self._date_submitted

        return d

