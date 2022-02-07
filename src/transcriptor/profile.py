import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class Profile:
    """Class containing information about user profile."""

    first_name: str = ""
    last_name: str = ""
    area: str = ""
    country: str = ""

    def __post_init__(self):
        self.full_name = "%s %s" % (self.first_name, self.last_name)

    def to_dict(self) -> dict:
        """
        Convert Profile instance to dictionary.

        Returns:
            A dictionary with profile details.
        """
        d: dict[Any, Any] = {}
        d["first_name"] = self.first_name
        d["last_name"] = self.last_name
        d["area"] = self.area
        d["country"] = self.country

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

    def save(self, config_path: Optional[Path]):
        """
        Write user profile to file.

        Arguments:
            config_path: Path to user profile file.
        """
        assert config_path is not None
        with open(config_path, "w") as fd:
            fd.write(self.to_json())

    @classmethod
    def load(cls, config_path: Optional[Path]):
        """
        Get user profile from file.

        Arguments:
            config_path: Path to user profile file.

        Returns:
            Profile instance
        """
        assert config_path is not None
        with open(config_path, "r") as fd:
            return cls(**json.load(fd))
