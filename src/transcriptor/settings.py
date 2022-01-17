import json
from pathlib import Path
from typing import Any, Optional, Union


class Settings:
    def __init__(
        self,
        clients_folder: Union[str, Path] = "",
        jobs_folder: Union[str, Path] = "",
        works_folder: Union[str, Path] = "",
        config_folder: Union[str, Path] = "",
        invoices_folder: Union[str, Path] = "",
        date_fmt: str = "",
    ):
        self.clients_folder = clients_folder
        self.jobs_folder = jobs_folder
        self.works_folder = works_folder
        self.date_fmt = date_fmt
        self.config_folder = config_folder
        self.invoices_folder = invoices_folder

    def to_dict(self) -> dict:
        d: dict[Any, Any] = {}
        d["clients_folder"] = str(self.clients_folder)
        d["jobs_folder"] = str(self.jobs_folder)
        d["works_folder"] = str(self.works_folder)
        d["date_fmt"] = str(self.date_fmt)
        d["config_folder"] = str(self.config_folder)
        d["invoices_folder"] = str(self.invoices_folder)

        return d

    def to_json(self, indent=2, ensure_ascii=False) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=ensure_ascii, sort_keys=True)

    @classmethod
    def from_json(cls, js: Optional[dict] = None):
        if js is None:
            return cls
        if not isinstance(js, dict):
            try:
                json.loads(js)
            except Exception:
                return cls()

        clients_folder: Union[str, Path] = "" if not "clients_folder" in js.keys() else Path(js["clients_folder"])
        jobs_folder: Union[str, Path] = "" if not "jobs_folder" in js.keys() else Path(js["jobs_folder"])
        works_folder: Union[str, Path] = "" if not "works_folder" in js.keys() else Path(js["works_folder"])
        config_folder: Union[str, Path] = "" if not "config_folder" in js.keys() else Path(js["config_folder"])
        invoices_folder: Union[str, Path] = "" if not "invoices_folder" in js.keys() else Path(js["invoices_folder"])
        date_fmt: str = "" if not "date_fmt" in js.keys() else js["date_fmt"]

        return cls(
            clients_folder=clients_folder,
            jobs_folder=jobs_folder,
            works_folder=works_folder,
            date_fmt=date_fmt,
            config_folder=config_folder,
            invoices_folder=invoices_folder,
        )
