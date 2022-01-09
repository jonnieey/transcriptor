from transcriptor.conf import get_config
from pathlib import Path

import json

config = get_config()

CLIENTS_FOLDER, JOBS_FOLDER, WORKS_FOLDER, CONFIG_FOLDER, DATE_FMT = (
    config['clients_folder'],
    config['jobs_folder'],
    config['works_folder'],
    config['config_folder'],
    config['date_fmt'],
)

class Settings:
    def __init__(self, clients_folder=None, jobs_folder=None, works_folder=None, date_fmt=None, config_folder=None):
        self.clients_folder = clients_folder
        self.jobs_folder = jobs_folder
        self.works_folder = works_folder
        self.date_fmt = date_fmt
        self.config_folder = config_folder

    @classmethod
    def generate_default_settings(cls):
        return cls(
            clients_folder = CLIENTS_FOLDER,
            config_folder  = CONFIG_FOLDER,
            jobs_folder    = JOBS_FOLDER,
            works_folder   = WORKS_FOLDER,
            date_fmt       = DATE_FMT,
        )

    def to_dict(self):
        d = {}
        d['clients_folder'] = str(self.clients_folder)
        d['jobs_folder']     = str(self.jobs_folder)
        d['works_folder']    = str(self.works_folder)
        d['date_fmt']    = str(self.date_fmt)
        d['config_folder']    = str(self.config_folder)

        return d

    def to_json(self, indent=2, ensure_ascii=False):
        return json.dumps(
            self.to_dict(),
            indent=indent,
            ensure_ascii=ensure_ascii,
            sort_keys=True,
        )

    @classmethod
    def from_json(cls, js=None):
        if js is None:
            return cls
        if type(js) is not dict:
            try:
                json.loads(js)
            except Exception:
                return cls()

        if 'clients_folder' in js.keys():
            clients_folder = Path(js['clients_folder'])
        else:
            clients_folder = None

        if 'jobs_folder' in js.keys():
            jobs_folder = Path(js['jobs_folder'])
        else:
            jobs_folder = None

        if 'works_folder' in js.keys():
            works_folder = Path(js['works_folder'])
        else:
            works_folder = None

        if 'config_folder' in js.keys():
            config_folder = Path(js['config_folder'])
        else:
            config_folder = None

        if 'date_fmt' in js.keys():
            date_fmt = js['date_fmt']
        else:
            date_fmt = None

        return cls(clients_folder=clients_folder, jobs_folder=jobs_folder, works_folder=works_folder, date_fmt=date_fmt, config_folder=config_folder)

    # make CONF_FILE editable by user
    def write_settings_to_file(self):
        settings_file = CONFIG_FOLDER / 'conf.json'
        if CONFIG_FOLDER.exists():
            with open(settings_file, 'w') as fp:
                fp.write(self.to_json())
        else:
            return

    def read_settings_from_file(self):
        settings_file = CONFIG_FOLDER / 'conf.json'
        if settings_file.exists() and not settings_file.is_dir():
            with open(settings_file, 'r') as fp:
                conf_json = json.load(fp)
                return self.from_json(conf_json)
        else:
            return
# if __name__  == "__main__":
