from datetime import date
from pathlib import Path
from tempfile import mkdtemp

import cmd2_ext_test
import pytest

from transcriptor.base import Transcriptor
from transcriptor.cli import TranscriptorCMD
from transcriptor.utils import str_to_date as std

today = date.today()


class TranscriptorTester(cmd2_ext_test.ExternalTestMixin, TranscriptorCMD):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


@pytest.fixture
def transcriptor_app():
    config = {"base_dir": mkdtemp(), "date_format": "%Y-%m-%d"}
    app = TranscriptorTester(Transcriptor(config=config))
    app.fixture_setup()
    yield app
    app.fixture_teardown()


def test_show_config(transcriptor_app):
    out = transcriptor_app.app_cmd("show config")
    assert "Date Format" in str(out.stdout).strip()
    assert "Base Dir" in str(out.stdout).strip()

    # update config
    cmd = "update config -b /tmp/testing -d %Y=%m=%d"
    transcriptor_app.app_cmd(cmd)
    out = transcriptor_app.app_cmd("show config")
    assert "testing" in str(out.stdout).strip()
    assert "%Y=%m=%d" in str(out.stdout).strip()


def test_show_profile(transcriptor_app):
    out = transcriptor_app.app_cmd("show profile")
    assert "First Name" in str(out.stdout).strip()
    assert "Country" in str(out.stdout).strip()
    assert "Area" in str(out.stdout).strip()

    cmd = "update profile -f TestFName -l TestLName -a TestArea -c TestCountry"
    transcriptor_app.app_cmd(cmd)
    out = transcriptor_app.app_cmd("show profile")
    assert "TestFName" in str(out.stdout).strip()
    assert "TestLName" in str(out.stdout).strip()
    assert "TestArea" in str(out.stdout).strip()
    assert "TestCountry" in str(out.stdout).strip()


def test_show_rates(transcriptor_app):
    cmd = "add client -n Anderson -e Anderson@gmail.com -r 0.3 0.4 0.5"
    transcriptor_app.app_cmd(cmd)
    out = transcriptor_app.app_cmd("show rates")
    assert "Expedite" in str(out.stdout).strip()
    assert "0.3" in str(out.stdout).strip()
    assert "Anderson" in str(out.stdout).strip()


def test_add_clients(transcriptor_app):
    # create clients
    out = transcriptor_app.app_cmd("show clients")
    assert "" == str(out.stdout).strip()
    cmd = "add client -n TestClient -e TestClient@gmail.com -r 0.3 0.4 0.5"
    transcriptor_app.app_cmd(cmd)
    out = transcriptor_app.app_cmd("show clients")
    assert "Client" in str(out.stdout).strip()
    assert "Email" in str(out.stdout).strip()
    assert "TestClient" in str(out.stdout).strip()
    assert "0.4" in str(out.stdout).strip()

    # update clients
    cmd = "update client -w name=TestClient -s name=TestNameClient email=TestEmail@gmail.com"
    transcriptor_app.app_cmd(cmd)
    out = transcriptor_app.app_cmd("show clients")
    assert "TestClient" not in str(out.stdout).strip()
    assert "TestNameClient" in str(out.stdout).strip()
    assert "TestEmail@gmail.com" in str(out.stdout).strip()
    assert "TestClient@gmail.com" not in str(out.stdout).strip()

    # delete clients
    cmd = "delete client -w client_id=1 -P"
    out = transcriptor_app.app_cmd(cmd)
    out = transcriptor_app.app_cmd("show clients")
    assert "TestClient" not in str(out.stdout).strip()
    assert "" == str(out.stdout).strip()


def test_add_job(transcriptor_app):
    # TODO use mocks
    cmd = "add client -n TestClient -e TestClient@gmail.com -r 0.3 0.4 0.5"
    transcriptor_app.app_cmd(cmd)
    cmd = "add job -c 1 -f '/home/kamikaze/.python/projects/transcriptor/tests/media_files/488460 BACKUP - 22 MINS.m4a' -r 2023-05-12 -d 2023-05-17 -w Yes -t Normal -T zd -N 'Testing one 2' -q 50"
    transcriptor_app.app_cmd(cmd)
    out = transcriptor_app.app_cmd("show jobs")
    assert "2023-05-12" in str(out.stdout).strip()
    assert "50" in str(out.stdout).strip()

    # update job
    cmd = "update jobs -s date_submitted=2023-05-16  status=Done -w 'id=1'"
    transcriptor_app.app_cmd(cmd)
    out = transcriptor_app.app_cmd("show jobs -a")
    # print(str(out.stdout).strip())
    assert today.strftime("%Y-%m-%d") not in str(out.stdout).strip()
    assert "2023-05-12" in str(out.stdout).strip()
    assert "Done" in str(out.stdout).strip()

    # delete job
    cmd = "delete jobs -w 'id>=1' -P"
    out = transcriptor_app.app_cmd(cmd)
    out = transcriptor_app.app_cmd("show jobs -a")
    assert "2023-05-16" not in str(out.stdout).strip()
    assert "2023-05-12" not in str(out.stdout).strip()
    assert "Done" not in str(out.stdout).strip()


def test_purge_jobs_delete_client(transcriptor_app):
    # TODO use mocks
    cmd = "add client -n TestClient -e TestClient@gmail.com -r 0.3 0.4 0.5"
    transcriptor_app.app_cmd(cmd)
    cmd = "add job -c 1 -f '/home/kamikaze/.python/projects/transcriptor/tests/media_files/488460 BACKUP - 22 MINS.m4a' -r 2023-05-12 -d 2023-05-17 -w Yes -t Normal -T zd -N 'Testing one 2' -q 50"
    transcriptor_app.app_cmd(cmd)
    cmd = "delete client -w client_id=1 -P"
    transcriptor_app.app_cmd(cmd)
    out = transcriptor_app.app_cmd("show clients")
    assert "TestClient" not in str(out.stdout).strip()
    assert "" == str(out.stdout).strip()
    out = transcriptor_app.app_cmd("show jobs")
    assert "2023-05-12" not in str(out.stdout).strip()
    assert "" == str(out.stdout).strip()


def test_purge_files(transcriptor_app):
    cmd = "add client -n TestClient -e TestClient@gmail.com -r 0.3 0.4 0.5"
    transcriptor_app.app_cmd(cmd)
    cmd = "add job -c 1 -f '/home/kamikaze/.python/projects/transcriptor/tests/media_files/488460 BACKUP - 22 MINS.m4a' -r 2023-05-12 -d 2023-05-17 -w Yes -t Normal -T zd -N 'Testing one 2' -q 50"
    transcriptor_app.app_cmd(cmd)
    date_r = std("2023-05-12", "%Y-%m-%d")
    date_d = std("2023-05-17", "%Y-%m-%d")
    job_file = Path(transcriptor_app.app.config.base_dir).joinpath(
        "clients",
        "TestClient",
        f"{date_r.year}",
        f'{date_r.strftime("%B")}',
        f"{date_r.strftime('%d_%a')}_488460_DUE_{date_d.strftime('%d_%a')}",
        "488460 BACKUP - 22 MINS.m4a",
    )
    assert job_file.exists() is True
    cmd = "purge -P -w 'job_id>=1'"
    transcriptor_app.app_cmd(cmd)
    assert job_file.exists() is False
