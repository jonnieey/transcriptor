import json
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Client:
    """Class containing information about a client."""

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
        """
        Convert client instance to dictionary.

        Returns:
            A dictionary with client details.
        """
        d: dict[Any, Any] = {}

        d["name"] = self.name
        d["email"] = self.email

        return d

    def to_json(self, indent=2, ensure_ascii=False) -> str:
        """
        Convert a dictionary to json.

        Arguments:
            indent: Json indent level.
            ensure_ascii: Escape non-ascii characters.

        Returns:
            Json object.
        """
        return json.dumps(
            self.to_dict(), indent=indent, ensure_ascii=ensure_ascii, sort_keys=True
        )

    @classmethod
    def from_json(cls, js: Optional[dict] = None):
        """
        Convert a json object to Client instance.

        Arguments:
            js: Client json object.

        Returns:
            Client instance.
        """
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
