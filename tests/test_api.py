import copy
import json
import shutil
import uuid
from datetime import datetime
from io import StringIO
from pathlib import Path

import pytest
import yaml
from sqlalchemy import select, text

from transcriptor.controller import API
from transcriptor.models import *
from transcriptor.utils import *

TODAY = datetime.today()
YEAR = TODAY.year

BASE_DIR = Path(__file__).parent.joinpath("data")


def config():
    date_format = "%m-%d-%Y"
    base_dir = str(BASE_DIR)
    config = ConfigModel(date_format, base_dir)
    return config


@pytest.fixture(name="test_config")
def test_config():
    return config()


@pytest.fixture()
def test_profile():
    first_name = "Fname"
    last_name = "Lname"
    area = "Area"
    country = "Country"
    return ProfileModel(first_name, last_name, area, country)


@pytest.fixture()
def test_client():
    name = "Client"
    email = "clientemail@gmail.com"
    rates = {"normal": 0.4, "expedite": 0.5, "interpreted": 0.3}
    rates = RatesModel(**rates)
    return ClientModel(name=name, email=email, rates=rates)


@pytest.fixture()
def test_job(test_client):
    job = JobModel(
        client_id=1,
        date_received="2022-05-05",
        job_number="56321",
        job_type="Normal",
        total_quantity="42.12630",
        job_rate="0.40",
        quantity="21.06315",
        date_due="2022-06-01",
        job_path="somerandompath",
    )
    return job


class TestApi:
    def setup_class(self):
        shutil.rmtree(BASE_DIR, ignore_errors=True)
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        self.api = API(config().base_dir)

    # def teardown_class(self):
    #     shutil.rmtree(BASE_DIR, ignore_errors=True)

    def test_save_config(self, test_config):
        fd = StringIO()
        self.api.save_config(test_config, fd)
        assert test_config == ConfigModel(**yaml.safe_load(fd.getvalue()))

    def test_load_config(self, test_config):
        fd = StringIO()
        self.api.save_config(test_config, fd)
        assert test_config == self.api.load_config(fd.getvalue())

    def test_save_profile(self, test_profile):
        fd = StringIO()
        self.api.save_profile(test_profile, fd)
        assert test_profile == ProfileModel(**yaml.safe_load(fd.getvalue()))

    def test_load_profile(self, test_profile):
        fd = StringIO()
        self.api.save_profile(test_profile, fd)
        assert test_profile == self.api.load_profile(fd.getvalue())

    def test_create_client(self):
        name, email, rates = (
            "name",
            "email@gmail.com",
            {"normal": 0.4, "expedite": 0.5, "interpreted": 0.3},
        )
        client = self.api.create_client(name, email, rates)
        assert isinstance(client, ClientModel)
        assert client.name == "name"
        assert client.id == None  # Not commited to db thus None

    def test_save_client(self, dbsession, test_client):
        self.api.save_client(test_client)
        stmt = text("""SELECT * from Clients where name = 'Client'""")
        client = dbsession.execute(stmt).first()
        assert client.name == "Client"

    def test_create_job(self):
        job_dict = {
            "client_id": 1,
            "date_received": "2022-05-05",
            "job_number": "56321",
            "job_type": "Normal",
            "total_quantity": "42.12630",
            "job_rate": "0.40",
            "quantity": "21.06315",
            "date_due": "2022-06-01",
            "job_path": "somerandompath",
        }
        job = self.api.create_job(**job_dict)
        assert job is not None
        assert isinstance(job, JobModel)

    def test_save_job(self, dbsession, test_job):
        self.api.save_job(test_job)
        stmt = text("""SELECT * from Jobs""")
        job = dbsession.execute(stmt).first()
        assert job is not None
        assert job.job_rate == 0.40
