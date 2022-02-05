import shutil
from pathlib import Path

import click
import pytest
from click.testing import CliRunner

from transcriptor.commands.client import cli as client_cli
from transcriptor.commands.job import cli as job_cli
from transcriptor.conf import get_config
from transcriptor.settings import Settings

settings = Settings(**get_config())

DATE_FMT, CLIENTS_FOLDER, JOBS_FOLDER, WORKS_FOLDER = (
    settings.date_fmt,
    settings.clients_folder,
    settings.jobs_folder,
    settings.works_folder,
)

expected = {"invalid_email": "Enter a valid email address"}


@pytest.fixture
def runner():
    return CliRunner()


class TestsClientCli:
    def setup_method(self):
        shutil.rmtree(CLIENTS_FOLDER.parent, ignore_errors=True)

    def teardown_method(self):
        shutil.rmtree(CLIENTS_FOLDER.parent, ignore_errors=True)

    def test_add_client(self, runner):
        result = runner.invoke(
            client_cli, ["add", "-n", "TestClient", "-e" "Testclient@gmail.com"]
        )
        assert result.exit_code == 0

    def test_valid_email(self, runner):
        result = runner.invoke(
            client_cli, ["add", "-n", "TestClient", "-e" "Testclientail.com"]
        )
        assert expected["invalid_email"] in result.output

    def test_missing_value_prompt(self, runner):
        result = runner.invoke(
            client_cli, ["add"], input="TestClient\nTestEmail@gmail.com"
        )
        assert result.exit_code == 0

    def test_list_clients(self, runner):
        runner.invoke(client_cli, ["add"], input="TestClient\nTestEmail@gmail.com")
        result = runner.invoke(client_cli, ["list"])
        expected = "TestClient"
        assert expected in result.output


class TestsJobCli:
    def teardown_method(self):
        shutil.rmtree(JOBS_FOLDER.parent, ignore_errors=True)

    def setup_method(self):
        CliRunner().invoke(client_cli, ["add"], input="TestClient\nTestEmail@gmail.com")

    def test_create_job(self, runner):
        expected = "Specify job type (Normal, Interpreted, Expedite):"
        result = runner.invoke(
            job_cli,
            [
                "create",
                "-f",
                str((Path(__file__).parent / "525529 Due 2.1 TT.zip")),
                "-c" "TestClient",
                "-r",
                0,
                "-d",
                4,
                "-n",
                "Test job cli",
            ],
            input="Y\nNormal\n\nzd\n",
        )
        assert expected in result.output

    def test_list_jobs(self, runner):
        expected = "525529"
        runner.invoke(
            job_cli,
            [
                "create",
                "-f",
                str((Path(__file__).parent / "525529 Due 2.1 TT.zip")),
                "-c" "TestClient",
                "-r",
                0,
                "-d",
                4,
                "-n",
                "Test job cli",
            ],
            input="Y\nNormal\n\nzd",
        )

        result = runner.invoke(job_cli, ["list", "-a"])
        # assert expected in result.output
        assert result.exit_code == 0

    def test_update(self, runner):
        runner.invoke(
            job_cli,
            [
                "create",
                "-f",
                str((Path(__file__).parent / "525529 Due 2.1 TT.zip")),
                "-c" "TestClient",
                "-r",
                0,
                "-d",
                4,
                "-n",
                "Test job cli",
            ],
            input="Y\nNormal\n\nzd",
        )
        runner.invoke(
            job_cli,
            [
                "update",
                "-r",
                "2022-01-01",
                "-d",
                "2022-01-05",
                "-a",
                "300",
                "-b",
                "2022-01-04",
                "525529",
            ],
        )
        result = runner.invoke(job_cli, ["list", "-a"])
        # assert "300" not in result.output
        # assert "2022-02-01" not in result.output
        # assert "2022-01-01" in result.output
        # assert "2022-01-05" in result.output
        assert result.exit_code == 0
