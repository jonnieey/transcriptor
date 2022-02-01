import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Optional, Union

from transcriptor.utils import date_to_string, string_to_date


@dataclass
class Job:
    date_received: Union[date, str] = ""
    job_number: str = ""
    job_type: str = ""
    total_quantity: float = 0.0
    job_rate: float = 0.0
    quantity: float = 0.0
    date_due: Union[date, str] = ""
    date_submitted: Union[date, str] = ""
    status: str = "Pending"
    amount_paid: float = 0.0
    job_path: Optional[Path] = None
    note: str = ""

    def __post_init__(self):
        # self.date_received = date_received if date_received else string_to_date(date_received))
        self.job_rate = (
            self.job_rate if self.job_rate else self.get_job_rate(self.job_type)
        )
        self.date_due = (
            self.date_due
            if self.date_due
            else self.get_date_due(self.date_received, self.job_type)
        )
        self.amount: float = round((self.job_rate * self.quantity), 0)
        self.amount_paid = (
            self.amount_paid if (self.amount_paid < self.amount) else self.amount
        )

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
    def amount(self) -> float:
        return self._amount

    @amount.setter
    def amount(self, value: float) -> None:
        self._amount = round(self.job_rate * self.quantity, 0)

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

        d["date_received"] = date_to_string(self.date_received)
        d["date_due"] = date_to_string(self.date_due)
        d["job_number"] = self.job_number
        d["job_type"] = self.job_type
        d["job_rate"] = self.job_rate
        d["total_quantity"] = self.total_quantity
        d["quantity"] = self.quantity
        d["status"] = self.status
        d["date_submitted"] = date_to_string(self.date_submitted)
        d["amount"] = self._amount
        d["amount_paid"] = self.amount_paid
        d["job_path"] = str(self.job_path)
        d["note"] = str(self.note)

        return d

    def to_json(self, indent=2, ensure_ascii=False) -> Union[str, dict]:
        return json.dumps(
            self.to_dict(),
            indent=indent,
            ensure_ascii=ensure_ascii,
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

        date_received: date = (
            "" if not "date_received" in js.keys() else js["date_received"]
        )
        date_due: date = "" if not "date_due" in js.keys() else js["date_due"]
        job_number: str = "" if not "job_number" in js.keys() else js["job_number"]
        job_type: str = "" if not "job_type" in js.keys() else js["job_type"]
        job_rate: float = 0.0 if not "job_rate" in js.keys() else js["job_rate"]
        total_quantity: float = (
            0.0 if not "total_quantity" in js.keys() else js["total_quantity"]
        )
        quantity: float = 0.0 if not "quantity" in js.keys() else js["quantity"]
        status: str = "" if not "status" in js.keys() else js["status"]
        date_submitted: date = (
            "" if not "date_submitted" in js.keys() else js["date_submitted"]
        )
        amount_paid: float = (
            0.0 if not "amount_paid" in js.keys() else js["amount_paid"]
        )
        job_path: Optional[Path] = (
            None if not "job_path" in js.keys() else js["job_path"]
        )
        note: str = "" if not "note" in js.keys() else js["note"]

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
            amount_paid=amount_paid,
            job_path=job_path,
            note=note,
        )
