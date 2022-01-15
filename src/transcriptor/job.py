import json
from datetime import date, timedelta

from transcriptor.utils import date_to_string, string_to_date


class Job:
    def __init__(
        self,
        date_received: date = None,
        job_number: str = "",
        job_type: str = "",
        total_quantity: float = 0.0,
        job_rate: float = None,
        quantity: float = 0.0,
        date_due: date = None,
        date_submitted: date = None,
        status: str = "Pending",
        amount: float = 0.0,
        amount_paid: float = 0.0,
        job_path=None,
    ) -> None:
        self.date_received = date_received
        self.job_number = job_number
        self.job_type = job_type
        self.total_quantity = total_quantity
        self.quantity = quantity
        self.date_submitted = date_submitted
        self.status = status
        self.job_rate = job_rate
        self.date_due = date_due
        self.amount = amount
        self.job_path = job_path
        self.amount_paid = amount_paid

        if amount_paid > self.amount:
            self.amount_paid = self.amount

        if date_due is None and job_type:
            date_due = self.get_date_due(date_received, job_type)
            self.date_due = date_due

        elif isinstance(date_due, str):
            date_due = string_to_date(date_due)
            self.date_due = date_due

        if job_rate is None and job_type:
            job_rate = self.get_job_rate(job_type)
            self.job_rate = job_rate

    @property
    def date_received(self):
        return self._date_received

    @date_received.setter
    def date_received(self, value):
        self._date_received = value

    @property
    def job_number(self) -> str:
        return self._job_number

    @job_number.setter
    def job_number(self, value):
        self._job_number = value

    @property
    def job_type(self) -> str:
        return self._job_type

    @job_type.setter
    def job_type(self, value):
        self._job_type = value

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

    @property
    def amount(self):
        return self._amount

    @amount.setter
    def amount(self, value):
        self._amount = value

    @property
    def amount_paid(self):
        return self._amount_paid

    @amount_paid.setter
    def amount_paid(self, value):
        self._amount_paid = value

    @property
    def job_path(self):
        return self._job_path

    @job_path.setter
    def job_path(self, value):
        self._job_path = value

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
        job_types = {"Normal": 5, "Interpreted": 5, "Expedite": 1}
        job_days = job_types[job_type]
        due_date = date_received + timedelta(days=job_days)
        return due_date

    def get_job_rate(self, job_type):
        job_types = {"Normal": 0.4, "Interpreted": 0.3, "Expedite": 0.6}
        return job_types[job_type]

    def to_dict(self):
        d = {}

        d["date_received"] = date_to_string(self._date_received)
        d["date_due"] = date_to_string(self._date_due)
        d["job_number"] = self._job_number
        d["job_type"] = self._job_type
        d["job_rate"] = self._job_rate
        d["total_quantity"] = self._total_quantity
        d["quantity"] = self._quantity
        d["status"] = self._status
        d["date_submitted"] = date_to_string(self._date_submitted)
        d["amount"] = self._amount
        d["amount_paid"] = self._amount_paid
        d["job_path"] = str(self._job_path)

        return d

    def to_json(self, indent=2, ensure_ascii=False):
        return json.dumps(
            self.to_dict(),
            indent=indent,
            ensure_ascii=ensure_ascii,
            # sort_keys=True,
        )

    @classmethod
    def from_json(cls, js=None):
        if js is None:
            return cls()

        if type(js) is not dict:
            try:
                js = json.loads(js)
            except Exception:
                return cls()

        if "date_received" in js.keys():
            date_received = js["date_received"]
        else:
            date_received = None

        if "date_due" in js.keys():
            date_due = js["date_due"]
        else:
            date_due = None

        if "job_number" in js.keys():
            job_number = js["job_number"]
        else:
            job_number = None

        if "job_type" in js.keys():
            job_type = js["job_type"]
        else:
            job_type = None

        if "job_rate" in js.keys():
            job_rate = js["job_rate"]
        else:
            job_rate = None

        if "total_quantity" in js.keys():
            total_quantity = js["total_quantity"]
        else:
            total_quantity = None

        if "quantity" in js.keys():
            quantity = js["quantity"]
        else:
            quantity = None
        if "status" in js.keys():
            status = js["status"]
        else:
            status = None

        if "date_submitted" in js.keys():
            date_submitted = js["date_submitted"]
        else:
            date_submitted = None

        if "amount" in js.keys():
            amount = js["amount"]
        else:
            amount = None

        if "amount_paid" in js.keys():
            amount_paid = js["amount_paid"]
        else:
            amount_paid = None

        if "job_path" in js.keys():
            job_path = js["job_path"]
        else:
            job_path = None

        return cls(
            date_received=date_received,
            job_number=job_number,
            job_type=job_type,
            total_quantity=total_quantity,
            job_rate=job_rate,
            quantity=quantity,
            date_due=date_due,
            date_submitted=date_submitted,
            status=status,
            amount=amount,
            amount_paid=amount_paid,
            job_path=job_path,
        )
