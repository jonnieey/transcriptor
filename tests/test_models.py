import uuid
from collections.abc import Iterable
from io import StringIO
from pathlib import Path

import pytest
import yaml

from transcriptor.models import *


@pytest.fixture()
def test_config_model():
    date_format = "%Y-%m-%d"
    base_dir = str(Path(__file__).parent.joinpath("data"))
    return ConfigModel(date_format, base_dir)


@pytest.fixture()
def test_profile_model():
    first_name = "Test"
    last_name = "Profile"
    area = "Area"
    country = "Country"
    return ProfileModel(first_name, last_name, area, country)


@pytest.fixture()
def test_client_model():
    name = "Client"
    email = "clientemail@gmail.com"
    rates = {"Normal": 0.4, "Expedite": 0.5, "Interpreted": 0.3}
    return ClientModel(client_id, name, email, rates)


@pytest.fixture()
def test_job_model():
    job = JobModel(
        job_id=str(uuid.uuid4()),
        client_id=str(uuid.uuid4()),
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


class TestConfigModel:
    def test_base_dir_is_str(self, test_config_model):
        assert isinstance(test_config_model.base_dir, str)

    def test_is_iterable(self, test_config_model):
        assert isinstance(test_config_model, Iterable)

    def test_get_attribute(self, test_config_model):
        assert test_config_model.get("date_format") == "%Y-%m-%d"
        assert test_config_model.date_format == "%Y-%m-%d"

    def test_set_attribute(self, test_config_model):
        test_config_model.date_format = "%m-%d-%Y"
        assert test_config_model.date_format != "%Y-%m-%d"
        assert test_config_model.date_format == "%m-%d-%Y"

    def test_save(self, test_config_model):
        fd = StringIO()
        test_config_model.save(fd)
        assert test_config_model == ConfigModel(**yaml.safe_load(fd.getvalue()))


class TestProfileModel:
    def test_is_iterable(self, test_profile_model):
        assert isinstance(test_profile_model, Iterable)

    def test_get_attribute(self, test_profile_model):
        assert test_profile_model.country == "Country"
        assert test_profile_model.get("area") == "Area"

    def test_set_attribute(self, test_profile_model):
        test_profile_model.country = "Country2"
        assert test_profile_model.country != "Country"
        assert test_profile_model.country == "Country2"

    def test_save(self, test_profile_model):
        fd = StringIO()
        test_profile_model.save(fd)
        assert test_profile_model == ProfileModel(**yaml.safe_load(fd.getvalue()))
