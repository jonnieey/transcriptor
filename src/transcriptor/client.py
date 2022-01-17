import json
from typing import Any, Optional


class Client:
    def __init__(self, name: str = "", email: str = "") -> None:
        self.name = name
        self.email = email

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        self._email = value

    def __str__(self) -> str:
        return "%s" % (self._name)

    def to_dict(self) -> dict:
        d: dict[Any, Any] = {}

        d["name"] = self._name
        d["email"] = self._email

        return d

    def to_json(self, indent=2, ensure_ascii=False) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=ensure_ascii, sort_keys=True)

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
