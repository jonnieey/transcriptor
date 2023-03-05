#!/usr/bin/python3
import shutil
import tempfile

import cmd2_ext_test
import pytest

from transcriptor.base import Transcriptor
from transcriptor.cli2 import TranscriptorCMD
from transcriptor.models import ConfigModel


class TranscriptorTester(cmd2_ext_test.ExternalTestMixin, TranscriptorCMD):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


@pytest.fixture
def transcriptor_app():
    temp_dir = tempfile.mkdtemp()
    CONFIG = {"date_format": "%Y-%m-%d", "base_dir": f"{temp_dir}"}
    config = ConfigModel(**CONFIG)
    app = TranscriptorTester(app=Transcriptor(config))
    app.fixture_setup()
    yield app
    shutil.rmtree(temp_dir)
    app.fixture_teardown()


class TestConfig:
    def test_print_help(self, transcriptor_app):
        out = transcriptor_app.app_cmd("help")

        assert "Documented commands" in out.stdout.strip()
        assert "show" in out.stdout.strip()
        assert "add" in out.stdout.strip()
        assert "update" in out.stdout.strip()
        assert "delete" in out.stdout.strip()

    def test_config(self, transcriptor_app):

        bak_base_dir = transcriptor_app.app.config.base_dir

        # show config help
        out = transcriptor_app.app_cmd("help show config")
        assert "show config" in out.stdout.strip()

        # show config
        out = transcriptor_app.app_cmd("show config")
        assert "Date Format" in out.stdout.strip()
        assert "Base Dir" in out.stdout.strip()
        assert f"{transcriptor_app.app.config.base_dir}" in out.stdout.strip()

        # update config
        transcriptor_app.app_cmd("update config -b temp_dir")
        out = transcriptor_app.app_cmd("show config")
        assert "temp_dir" in out.stdout.strip()

        # update config
        transcriptor_app.app_cmd(f"update config -b {bak_base_dir}")
        out = transcriptor_app.app_cmd("show config")
        assert "temp_dir" not in out.stdout.strip()

    def test_profile(self, transcriptor_app):
        # show config help
        out = transcriptor_app.app_cmd("help show profile")
        assert "show profile" in out.stdout.strip()

        # show profile
        out = transcriptor_app.app_cmd("show profile")
        assert "First Name" in out.stdout.strip()
        assert "Last Name" in out.stdout.strip()
        assert "Area" in out.stdout.strip()
        assert "Country" in out.stdout.strip()

        # update profile
        transcriptor_app.app_cmd("update profile -f first_name")
        transcriptor_app.app_cmd("update profile -l last_name")
        transcriptor_app.app_cmd("update profile -a Miami")
        transcriptor_app.app_cmd("update profile -c America")

        out = transcriptor_app.app_cmd("show profile")
        assert "first_name" in out.stdout.strip()
        assert "last_name" in out.stdout.strip()
        assert "Miami" in out.stdout.strip()
        assert "America" in out.stdout.strip()

    def test_add_client(self, transcriptor_app):
        # add client using key=value string rates
        transcriptor_app.app_cmd(
            "add client -n first_client -e first_client@email.com -r 'normal=0.4 expedite=0.6 interpreted=0.3'"
        )

        # show client
        out = transcriptor_app.app_cmd("show clients")
        assert "first_client" in out.stdout.strip()
        assert "first_client@email.com" in out.stdout.strip()
        assert "0.4" in out.stdout.strip()
        assert "0.3" in out.stdout.strip()
        assert "0.6" in out.stdout.strip()

        # add client using dict string rates
        transcriptor_app.app_cmd(
            """add client -n second_client -e second_client@email.com -r '{"normal":0.45, "expedite":0.65, "interpreted":0.35}'"""
        )
        out = transcriptor_app.app_cmd("show clients")
        assert "second_client" in out.stdout.strip()
        assert "0.45" in out.stdout.strip()
        assert "0.35" in out.stdout.strip()
        assert "0.65" in out.stdout.strip()

        # update client
        transcriptor_app.app_cmd(
            """update client -i 1 -n third_client -e third_client@email.com -r '{"normal":0.48, "expedite":0.68, "interpreted":0.38}'"""
        )
        out = transcriptor_app.app_cmd("show clients")
        assert "third_client" in out.stdout.strip()
        assert "first_client" not in out.stdout.strip()
        assert "0.48" in out.stdout.strip()
        assert "0.68" in out.stdout.strip()
        assert "0.38" in out.stdout.strip()

        # delete client
        # add flag to delete client without prompt
        # transcriptor_app.app_cmd("delete client -i 1")
        # out = transcriptor_app.app_cmd("show clients")
        # assert "third_client" not in out.stdout.strip()
