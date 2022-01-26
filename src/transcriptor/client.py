import json
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Client:
    name: str = ""
    email: str = ""

    def __eq__(self, other: object) -> bool:

        equal = False

        if isinstance(other, Client):
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

    def __str__(self) -> str:
        return "%s" % (self.name)

    def to_dict(self) -> dict:
        d: dict[Any, Any] = {}

        d["name"] = self.name
        d["email"] = self.email

        return d

    def to_json(self, indent=2, ensure_ascii=False) -> str:
        return json.dumps(
            self.to_dict(), indent=indent, ensure_ascii=ensure_ascii, sort_keys=True
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

        name: str = "" if not "name" in js.keys() else js["name"]
        email: str = "" if not "email" in js.keys() else js["email"]

        return cls(name=name, email=email)
