import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Profile:
    first_name: str = ""
    last_name: str = ""
    area: str = ""
    country: str = ""

    def __post_init__(self):
        self.full_name = "%s %s" % (self.first_name, self.last_name)

    def to_dict(self) -> dict:
        d: dict[Any, Any] = {}
        d["first_name"] = self.first_name
        d["last_name"] = self.last_name
        d["area"] = self.area
        d["country"] = self.country

        return d

    def to_json(self, indent=2, ensure_ascii=False) -> str:
        return json.dumps(
            self.to_dict(), indent=indent, ensure_ascii=ensure_ascii, sort_keys=True
        )

    def save(self, config_path: Path):
        with open(config_path, "w") as fd:
            fd.write(self.to_json())

    @classmethod
    def load(cls, config_path: Path):
        with open(config_path, "r") as fd:
            return cls(**json.load(fd))
