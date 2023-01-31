import shutil
from datetime import datetime
from io import StringIO
from pathlib import Path

import pytest
import yaml
from sqlalchemy import select
from sqlalchemy.engine.row import Row

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


class TestApi:
    def setup_class(self):
        shutil.rmtree(BASE_DIR, ignore_errors=True)
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        self.api = API(config().base_dir)

    # def teardown_class(self):
    #     shutil.rmtree(BASE_DIR, ignore_errors=True)
    @pytest.fixture()
    def test_job(self, test_client):
        job = self.api.create_job(
            client_id=1,
            date_received="2022-05-05",
            job_number="56321",
            job_type="normal",
            total_quantity="42.12630",
            job_rate="0.40",
            quantity="21.06315",
            date_due="2022-06-01",
            job_path="somerandompath",
        )
        return job

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
        stmt = select(ClientModel).where(ClientModel.name == "Client")
        client = dbsession.execute(stmt).scalar_one()
        assert client.name == "Client"

    def test_list_clients(self, dbsession):
        scalar = self.api.list_clients()
        assert isinstance(scalar, list)
        assert isinstance(scalar[0], Row)
        assert len(scalar) == 1

    def test_edit_client(self, dbsession, test_client):
        new_name = "New Client"
        new_email = "NewClient@gmail.com"
        new_rates = (0.45, 0.65, 0.35)

        self.api.edit_client(
            client_name=test_client.name,
            new_name=new_name,
            new_email=new_email,
            new_rates=new_rates,
        )
        stmt = select(ClientModel).where(ClientModel.id == 1)
        new_client = dbsession.execute(stmt).scalar_one()

        assert new_client.id == 1
        assert new_client.name == new_name
        assert new_client.email == new_email
        assert new_client.rates_id == 1

    def test_delete_client(self, dbsession):
        name, email, rates = (
            "name",
            "email@gmail.com",
            {"normal": 0.4, "expedite": 0.5, "interpreted": 0.3},
        )
        new_client = self.api.create_client(name, email, rates)
        self.api.save_client(new_client)
        stmt = select(ClientModel)
        clients = dbsession.execute(stmt).all()

        assert len(clients) == 2

        self.api.delete_client(client_name=name)
        clients = dbsession.execute(stmt).all()

        assert len(clients) == 1

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
        stmt = select(JobModel)
        job = dbsession.execute(stmt).first()

        assert job is not None
        assert job[0].job_rate == 0.40

    def test_list_jobs(self):
        job_scalars = self.api.list_jobs()

        assert isinstance(job_scalars, list)
        assert isinstance(job_scalars[0], Row)
        assert isinstance(job_scalars[0]._mapping["JobModel"], JobModel)

    def test_edit_job(self, dbsession, test_job):
        name, email, rates = (
            "name",
            "email@gmail.com",
            {"normal": 0.45, "expedite": 0.55, "interpreted": 0.35},
        )
        client = self.api.create_client(name, email, rates)
        self.api.save_client(client)
        stmt = select(ClientModel).where(ClientModel.name == name)

        new_client = dbsession.execute(stmt).scalar_one()
        new_job_dict = {"job_id": 1, "client_id": new_client.id}
        self.api.edit_job(**new_job_dict)

        stmt = select(JobModel).where(JobModel.id == 1)
        job = dbsession.execute(stmt).scalar_one()

        assert job.job_rate == 0.45
        assert job.client_id == 2

    def test_delete_job(self, dbsession):
        stmt = select(JobModel)
        jobs = dbsession.execute(stmt).all()
        stmt = select(JobModel).where(JobModel.id == 1)
        jobs = dbsession.execute(stmt).all()

        assert len(jobs) == 1
        self.api.delete_job(job_id=1)
        jobs = dbsession.execute(stmt).all()

        assert len(jobs) == 0

    def test_execute_sql(self, dbsession, test_job):
        self.api.save_job(test_job)
        stmt = select(JobModel)
        jobs = dbsession.execute(stmt).all()
        assert len(jobs) == 1

    def test_get_jobs_scalars_total(self, dbsession, test_job):
        self.api.save_job(test_job)
        stmt = select(JobModel)
        jobs = dbsession.execute(stmt).scalars()
        jobs_list = [job_row.__dict__ for job_row in jobs]
        amount, amount_paid = self.api.get_jobs_scalars_total(jobs_list)
        assert amount == 16.84  # Two jobs
        assert amount_paid == 0.0
