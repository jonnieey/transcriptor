import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union


@dataclass
class Settings:
    """Class containing information about user settings."""

    clients_folder: Optional[Path] = None
    jobs_folder: Optional[Path] = None
    works_folder: Optional[Path] = None
    config_folder: Optional[Path] = None
    invoices_folder: Optional[Path] = None
    resources_folder: Optional[Path] = None
    date_fmt: str = ""

    def __eq__(self, other: object) -> bool:

        equal = False

        if isinstance(other, Settings):
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

    def to_dict(self) -> dict:
        """
        Convert Settings instance to dictionary.

        Returns:
            A dictionary with settings details.
        """
        d: dict[Any, Any] = {}
        d["clients_folder"] = (
            str(self.clients_folder) if self.clients_folder is not None else ""
        )
        d["jobs_folder"] = str(self.jobs_folder) if self.jobs_folder is not None else ""
        d["works_folder"] = (
            str(self.works_folder) if self.works_folder is not None else ""
        )
        d["date_fmt"] = str(self.date_fmt)
        d["config_folder"] = (
            str(self.config_folder) if self.config_folder is not None else ""
        )
        d["invoices_folder"] = (
            str(self.invoices_folder) if self.invoices_folder is not None else ""
        )
        d["resources_folder"] = (
            str(self.resources_folder) if self.resources_folder is not None else ""
        )

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
        Convert a json object to Settings instance.

        Arguments:
            js: Settings json object.

        Returns:
            Settings instance.
        """
        if js is None:
            return cls
        if not isinstance(js, dict):
            try:
                json.loads(js)
            except Exception:
                return cls()

        clients_folder: Optional[Path] = (
            None if not "clients_folder" in js.keys() else Path(js["clients_folder"])
        )
        jobs_folder: Optional[Path] = (
            None if not "jobs_folder" in js.keys() else Path(js["jobs_folder"])
        )
        works_folder: Optional[Path] = (
            None if not "works_folder" in js.keys() else Path(js["works_folder"])
        )
        config_folder: Optional[Path] = (
            None if not "config_folder" in js.keys() else Path(js["config_folder"])
        )
        invoices_folder: Optional[Path] = (
            None if not "invoices_folder" in js.keys() else Path(js["invoices_folder"])
        )
        date_fmt: str = "" if not "date_fmt" in js.keys() else js["date_fmt"]
        resources_folder: Optional[Path] = (
            None
            if not "resources_folder" in js.keys()
            else Path(js["resources_folder"])
        )

        return cls(
            clients_folder=clients_folder,
            jobs_folder=jobs_folder,
            works_folder=works_folder,
            date_fmt=date_fmt,
            config_folder=config_folder,
            invoices_folder=invoices_folder,
            resources_folder=resources_folder,
        )

    def load(self, config_path: Optional[Path]):
        """
        Get settings from file.

        Arguments:
            config_path: Path to configuration file.

        Returns:
            Settings instance or None
        """
        if config_path:
            with open(config_path, "r") as fd:
                return self.from_json(json.load(fd))
        else:
            return

    def save(self, config_path: Optional[Path]) -> None:
        """
        Write settings to file.

        Arguments:
            config_path: Path to configuration file.
        """
        if config_path:
            with open(config_path, "w") as fd:
                fd.write(self.to_json())
        else:
            return
