#!/usr/bin/python3
import shutil
import tempfile
from pathlib import Path

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
    # app.app.api.db.engine.echo = True
    app.fixture_setup()
    yield app
    shutil.rmtree(temp_dir)
    app.fixture_teardown()


class TestConfig:
    def test_print_help(self, transcriptor_app):
        out = transcriptor_app.app_cmd("help")
        std_out = out.stdout.strip().strip("\n")

        assert "Documented commands" in std_out
        assert "show" in std_out
        assert "add" in std_out
        assert "update" in std_out
        assert "delete" in std_out

    def test_config(self, transcriptor_app):

        bak_base_dir = transcriptor_app.app.config.base_dir

        # show config help
        out = transcriptor_app.app_cmd("help show config")
        std_out = out.stdout.strip().strip("\n")
        assert "show config" in std_out

        # show config
        out = transcriptor_app.app_cmd("show config")
        std_out = out.stdout.strip().strip("\n")
        assert "Date Format" in std_out
        assert "Base Dir" in std_out
        assert f"{transcriptor_app.app.config.base_dir}" in std_out

        # update config
        transcriptor_app.app_cmd("update config -b temp_dir")
        out = transcriptor_app.app_cmd("show config")
        std_out = out.stdout.strip().strip("\n")
        assert "temp_dir" in std_out

        # update config
        transcriptor_app.app_cmd(f"update config -b {bak_base_dir}")
        out = transcriptor_app.app_cmd("show config")
        std_out = out.stdout.strip().strip("\n")
        assert "temp_dir" not in std_out

    def test_profile(self, transcriptor_app):
        # show config help
        out = transcriptor_app.app_cmd("help show profile")
        std_out = out.stdout.strip().strip("\n")
        assert "show profile" in std_out

        # show profile
        out = transcriptor_app.app_cmd("show profile")
        std_out = out.stdout.strip().strip("\n")
        assert "First Name" in std_out
        assert "Last Name" in std_out
        assert "Area" in std_out
        assert "Country" in std_out

        # update profile
        transcriptor_app.app_cmd("update profile -f 'first name'")
        transcriptor_app.app_cmd("update profile -l last_name")
        transcriptor_app.app_cmd("update profile -a Miami")
        transcriptor_app.app_cmd("update profile -c America")

        out = transcriptor_app.app_cmd("show profile")
        std_out = out.stdout.strip().strip("\n")
        assert "first name" in std_out
        assert "last_name" in std_out
        assert "Miami" in std_out
        assert "America" in std_out

    def test_client(self, transcriptor_app):
        # add client using key=value string rates
        transcriptor_app.app_cmd(
            "add client -n first_client -e first_client@email.com -r 'normal=0.4 expedite=0.6 interpreted=0.3'"
        )

        # show client
        out = transcriptor_app.app_cmd("show clients")
        std_out = out.stdout.strip().strip("\n")
        assert "first_client" in std_out
        assert "first_client@email.com" in std_out
        assert "0.4" in std_out
        assert "0.3" in std_out
        assert "0.6" in std_out

        # add client using dict string rates
        transcriptor_app.app_cmd(
            """add client -n second_client -e second_client@email.com -r '{"normal":0.45, "expedite":0.65, "interpreted":0.35}'"""
        )
        out = transcriptor_app.app_cmd("show clients")
        std_out = out.stdout.strip().strip("\n")
        assert "second_client" in std_out
        assert "0.45" in std_out
        assert "0.35" in std_out
        assert "0.65" in std_out

        # update client
        transcriptor_app.app_cmd(
            """update client -i 1 -n third_client -e third_client@email.com -r '{"normal":0.48, "expedite":0.68, "interpreted":0.38}'"""
        )
        out = transcriptor_app.app_cmd("show clients")
        std_out = out.stdout.strip().strip("\n")
        assert "third_client" in std_out
        assert "first_client" not in std_out
        assert "0.48" in std_out
        assert "0.68" in std_out
        assert "0.38" in std_out

        # delete client
        transcriptor_app.app_cmd("delete client -i 1 -y")
        out = transcriptor_app.app_cmd("show clients")
        std_out = out.stdout.strip().strip("\n")
        assert "third_client" not in std_out

    def test_job(self, transcriptor_app):
        media_file = Path(__file__).parent.joinpath("media_files", "Sample.m4a")
        media_file2 = shutil.copy(
            media_file, f"{transcriptor_app.app.config.base_dir}/222222-Due-2.7.m4a"
        )

        # Create client
        transcriptor_app.app_cmd(
            "add client -n first_client -e first_client@email.com -r 'normal=0.4 expedite=0.6 interpreted=0.3'"
        )
        # Create job
        transcriptor_app.app_cmd(
            f"add job -c first_client -f {media_file2} -r 2023-02-02 -d 2023-02-07 -q 50 -w yes -t Normal -T zd -N 'Cannot be late'"
        )
        out = transcriptor_app.app_cmd("show jobs")
        std_out = out.stdout.strip().strip("\n")
        assert "222222" in std_out
        assert "first_client" not in std_out
        assert "2023-02-02" in std_out
        assert "2023-02-07" in std_out
        assert "Normal" in std_out
        assert "Cannot be" in std_out
        assert "late" in std_out

        # Update Job
        transcriptor_app.app_cmd(
            f"update job -i 1 -r 2023-02-03 -d 2023-02-08 -n 222220 -t Expedite -S 2023-02-07 -R 0.2 -q 40"
        )
        # Use --all flag since only pending jobs are shown by default
        out = transcriptor_app.app_cmd("show jobs -a")
        std_out = out.stdout.strip().strip("\n")
        assert "222222" not in std_out
        assert "2023-02-03" in std_out
        assert "2023-02-08" in std_out
        assert "Normal" not in std_out
        assert "Expedite" in std_out
        assert "Done" in std_out  # updating date_submitted updates status
        assert "2023-02-07" in std_out
        assert "0.2" in std_out  # cmd args take precedence over client rates value
        assert "8.0" in std_out  # cmd args take precedence over client rates value

        transcriptor_app.app_cmd(
            "add client -n second_client -e second_client@email.com -r 'normal=0.45 expedite=0.65 interpreted=0.35'"
        )
        transcriptor_app.app_cmd(f"update job -i 1 -c 2")

        out = transcriptor_app.app_cmd("show jobs -a")
        std_out = out.stdout.strip().strip("\n")
        assert "│ 2         │" in std_out  # client id, many 2s in stdout
        assert "0.65" in std_out
        assert "26.0" in std_out  # 40 (quantity) * 0.65 (expedite)

        # delete job
        transcriptor_app.app_cmd(f"delete job -i 1 -y")
        out = transcriptor_app.app_cmd("show jobs -a")
        std_out = out.stdout.strip().strip("\n")
        assert "** No Jobs **" in std_out
