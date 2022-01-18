import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Optional, Union

from transcriptor.utils import date_to_string, string_to_date


class Job:
    def __init__(
        self,
        date_received: Union[str, date] = "",
        job_number: str = "",
        job_type: str = "",
        total_quantity: float = 0.0,
        job_rate: float = 0.0,
        quantity: float = 0.0,
        date_due: Union[str, date] = "",
        date_submitted: Union[str, date] = "",
        status: str = "Pending",
        amount: float = 0.0,
        job_path: Union[str, Path] = "",
        amount_paid: float = 0.0,
    ) -> None:
        self.date_received = date_received if isinstance(date_received, date) else string_to_date(date_received)
        self.job_number = job_number
        self.job_type = job_type
        self.total_quantity = total_quantity
        self.quantity = quantity
        self.date_submitted = date_submitted if isinstance(date_submitted, date) else string_to_date(date_submitted)
        self.status = status
        self.job_path = job_path
        self.job_rate = job_rate
        self.date_due = date_due if isinstance(date_due, date) else string_to_date(date_due)
        self.amount = amount
        self.amount_paid = amount_paid

        if not amount and job_rate and quantity:
            self.amount: float = job_rate * quantity

        if amount_paid > self.amount:
            self.amount_paid: float = self.amount
        if not date_due and job_type:
            date_due = self.get_date_due(date_received, job_type)
            self.date_due: date = date_due

        if not job_rate and job_type:
            job_rate = self.get_job_rate(job_type)
            self.job_rate: float = job_rate

    def __eq__(self, other: object) -> bool:

        equal = False

        if isinstance(other, Job):
            if self.to_dict() == other.to_dict():
                equal = True
            else:
                equal = False
        elif isinstance(other, dict):
            if self.to_dict() == other:
                equal = True
            else:
                equal = False

        return equal

    @property
    def date_received(self) -> Union[str, date]:
        return self._date_received

    @date_received.setter
    def date_received(self, value: Union[str, date]) -> None:
        self._date_received = value

    @property
    def job_number(self) -> str:
        return self._job_number

    @job_number.setter
    def job_number(self, value: str) -> None:
        self._job_number = value

    @property
    def job_type(self) -> str:
        return self._job_type

    @job_type.setter
    def job_type(self, value: str) -> None:
        self._job_type = value

    @property
    def job_rate(self) -> float:
        return self._job_rate

    @job_rate.setter
    def job_rate(self, value: float) -> None:
        self._job_rate = value

    @property
    def quantity(self) -> float:
        return self._quantity

    @quantity.setter
    def quantity(self, value: float) -> None:
        self._quantity = value

    @property
    def total_quantity(self) -> float:
        return self._total_quantity

    @total_quantity.setter
    def total_quantity(self, value: float) -> None:
        self._total_quantity = value

    @property
    def date_due(self) -> Union[str, date]:
        return self._date_due

    @date_due.setter
    def date_due(self, value: Union[str, date]) -> None:
        self._date_due = value

    @property
    def date_submitted(self) -> Union[str, date]:
        return self._date_submitted

    @date_submitted.setter
    def date_submitted(self, value: Union[str, date]) -> None:
        self._date_submitted = value

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        self._status = value

    @property
    def amount(self) -> float:
        return self._amount

    @amount.setter
    def amount(self, value: float) -> None:
        self._amount = value

    @property
    def amount_paid(self) -> float:
        return self._amount_paid

    @amount_paid.setter
    def amount_paid(self, value: float) -> None:
        self._amount_paid = value

    @property
    def job_path(self) -> Union[str, Path]:
        return self._job_path

    @job_path.setter
    def job_path(self, value: Path) -> None:
        self._job_path = value

    def __str__(self) -> str:
        j = "%s %s %s %s %s %s" % (
            self.job_number,
            self.date_received,
            self.job_type,
            self.quantity,
            self.job_rate,
            self.date_due,
        )
        return j

    def get_date_due(self, date_received: Union[str, date], job_type: str) -> date:
        job_types = {"Normal": 5, "Interpreted": 5, "Expedite": 1}
        job_days = job_types[job_type]

        if isinstance(date_received, date):
            due_date = date_received + timedelta(days=job_days)

        elif isinstance(date_received, str):
            d = string_to_date(date_received)
            if isinstance(d, date):
                due_date = d + timedelta(days=job_days)
            elif isinstance(d, str) and d:
                d_obj = string_to_date(d)
                if isinstance(d_obj, date):
                    due_date = d_obj + timedelta(days=job_days)

        return due_date

    def get_job_rate(self, job_type: str) -> float:
        job_types = {"Normal": 0.4, "Interpreted": 0.3, "Expedite": 0.6}
        return job_types[job_type]

    def to_dict(self) -> dict[Any, Any]:
        d: dict[Any, Any] = {}

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

    def to_json(self, indent=2, ensure_ascii=False) -> Union[str, dict]:
        return json.dumps(
            self.to_dict(),
            indent=indent,
            ensure_ascii=ensure_ascii,
            # sort_keys=True,
        )

    @classmethod
    def from_json(cls, js: Optional[dict] = None):
        if js is None:
            return cls()

        if not isinstance(js, dict):
            try:
                js = json.loads(js)
            except Exception:
                return cls()

        date_received: date = "" if not "date_received" in js.keys() else js["date_received"]
        date_due: date = "" if not "date_due" in js.keys() else js["date_due"]
        job_number: str = "" if not "job_number" in js.keys() else js["job_number"]
        job_type: str = "" if not "job_type" in js.keys() else js["job_type"]
        job_rate: float = 0.0 if not "job_rate" in js.keys() else js["job_rate"]
        total_quantity: float = 0.0 if not "total_quantity" in js.keys() else js["total_quantity"]
        quantity: float = 0.0 if not "quantity" in js.keys() else js["quantity"]
        status: str = "" if not "status" in js.keys() else js["status"]
        date_submitted: date = "" if not "date_submitted" in js.keys() else js["date_submitted"]
        amount: float = 0.0 if not "amount" in js.keys() else js["amount"]
        amount_paid: float = 0.0 if not "amount_paid" in js.keys() else js["amount_paid"]
        job_path: Union[str, Path] = "" if not "job_path" in js.keys() else js["job_path"]

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
