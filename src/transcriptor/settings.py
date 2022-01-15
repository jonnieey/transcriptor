import json
from pathlib import Path


class Settings:
    def __init__(
        self,
        clients_folder=None,
        jobs_folder=None,
        works_folder=None,
        date_fmt=None,
        config_folder=None,
        invoices_folder=None,
    ):
        self.clients_folder = clients_folder
        self.jobs_folder = jobs_folder
        self.works_folder = works_folder
        self.date_fmt = date_fmt
        self.config_folder = config_folder
        self.invoices_folder = invoices_folder

    def to_dict(self):
        d = {}
        d["clients_folder"] = str(self.clients_folder)
        d["jobs_folder"] = str(self.jobs_folder)
        d["works_folder"] = str(self.works_folder)
        d["date_fmt"] = str(self.date_fmt)
        d["config_folder"] = str(self.config_folder)
        d["invoices_folder"] = str(self.invoices_folder)

        return d

    def to_json(self, indent=2, ensure_ascii=False):
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=ensure_ascii, sort_keys=True)

    @classmethod
    def from_json(cls, js=None):
        if js is None:
            return cls
        if type(js) is not dict:
            try:
                json.loads(js)
            except Exception:
                return cls()

        if "clients_folder" in js.keys():
            clients_folder = Path(js["clients_folder"])
        else:
            clients_folder = None

        if "jobs_folder" in js.keys():
            jobs_folder = Path(js["jobs_folder"])
        else:
            jobs_folder = None

        if "works_folder" in js.keys():
            works_folder = Path(js["works_folder"])
        else:
            works_folder = None

        if "config_folder" in js.keys():
            config_folder = Path(js["config_folder"])
        else:
            config_folder = None

        if "invoices_folder" in js.keys():
            invoices_folder = Path(js["invoices_folder"])
        else:
            invoices_folder = None

        if "date_fmt" in js.keys():
            date_fmt = js["date_fmt"]
        else:
            date_fmt = None

        return cls(
            clients_folder=clients_folder,
            jobs_folder=jobs_folder,
            works_folder=works_folder,
            date_fmt=date_fmt,
            config_folder=config_folder,
            invoices_folder=invoices_folder,
        )
