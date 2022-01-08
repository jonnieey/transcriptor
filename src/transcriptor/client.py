import json

class Client:
    def __init__(self, name : str='', email: str=''):
        self.name = name
        self.email = email

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        self._email = value

    def __str__(self):
        return '%s' % (self._name)

    def to_dict(self):
        d = {}

        d['name'] = self._name
        d['email'] = self._email

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
            return cls()

        if type(js) is not dict:
            try:
                js = json.loads(js)
            except Exception:
                return cls()

        if 'name' in js.keys():
            name = js['name']
        else:
            name = ''

        if 'email' in js.keys():
            email = js['email']
        else:
            email = ''

        return cls(name=name, email=email)

