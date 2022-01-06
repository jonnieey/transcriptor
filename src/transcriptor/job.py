from datetime import timedelta, datetime
import json
from transcriptor.client import Client

class Job:
    def __init__(
        self,
        date_received: str,
        job_number: str,
        type : str,
        quantity : float= 0.0,
        date_due: str = '',
        date_submitted: str = '' ,
        media_files: list = [],
        status: str = 'Pending',
    ) -> None:
        self.date_received = date_received
        self.job_number = job_number
        self.type = type
        self.rate = self.get_job_details(type)['rate']
        self.quantity = quantity
        self.date_due = date_due if date_due != '' else self.get_date_due(type)
        self.date_submitted = date_submitted
        self.media_files = media_files
        self.status = status

    @property
    def type(self) -> str:
        return self._type

    @type.setter
    def type(self, value):
        self._type = value
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
    def media_files(self):
        return self._media_files

    @media_files.setter
    def media_files(self, value):
        self._media_files = value

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

    def get_date_due(self, type: str ):
        due_date = (datetime.today() + timedelta(abs(self.get_job_details(type)['due_in']))).strftime("%Y-%m-%d")
        return due_date

    def __str__(self):
        j = "%s %s %s %s %s %s %s" % (
            self.job_number,
            self.date_received,
            self.type,
            self.quantity,
            self.media_files,
            self.rate,
            self.date_due,
        )
        return j

    def to_dict(self):
        d = {}

        d['date_received'] = self._date_received
        d['job_number'] = self._job_number
        d['type'] = self._type
        d['rate'] = self._rate
        d['quantity'] = self._quantity
        d['date_due'] = self._date_due
        d['date_submitted'] = self._date_submitted
        d['media_files'] = self._media_files
        d['status'] = self._status

        return d

    def to_json(self, indent=2, ensure_ascii=False):
        return json.dumps(
            self.to_dict(),
            indent=indent,
            ensure_ascii=ensure_ascii,
            sort_keys=True,
        )

if __name__ == "__main__":
    client = Client('Anderson', 'Anderson@gmail.com')
    job = Job(date_received = datetime.today().strftime('%Y-%m-%d'), job_number = '56321', type = 'Normal')
    print(job.to_dict())


