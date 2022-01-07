from transcriptor import CLIENT_FOLDER, JOB_FOLDER, WORK_FOLDER, CONF_FILE
import json
from pathlib import Path

class Settings:
    def __init__(self, clients_folder=None, job_folder=None, work_folder=None):
        self.clients_folder = clients_folder
        self.job_folder = job_folder
        self.work_folder = work_folder

    @classmethod
    def generate_default_settings(cls):
        return cls(
            clients_folder=CLIENT_FOLDER,
            job_folder=JOB_FOLDER,
            work_folder=WORK_FOLDER,
        )

    def to_dict(self):
        d = {}
        d['clients_folder'] = self.clients_folder
        d['job_folder'] = self.job_folder
        d['work_folder'] = self.work_folder

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
            clients_folder = js['clients_folder']
        else:
            clients_folder = None

        if 'job_folder' in js.keys():
            job_folder = js['job_folder']
        else:
            job_folder = None

        if 'work_folder' in js.keys():
            work_folder = js['work_folder']
        else:
            work_folder = None

        return cls(clients_folder=clients_folder, job_folder=job_folder, work_folder=work_folder)

    # make CONF_FILE editable by user
    def write_settings_to_file(self):
        settings_file = Path(CONF_FILE) / 'conf.json'
        with open(settings_file, 'w') as fp:
            fp.write(self.to_json())

    def read_settings_from_file(self):
        settings_file = Path(CONF_FILE) / 'conf.json'
        with open(settings_file, 'r') as fp:
            conf_json = json.load(fp)
            return self.from_json(conf_json)


