import pytest
from click.testing import CliRunner

from transcriptor.commands.clients import cli as clients_cli
from transcriptor.commands.config import cli as config_cli
from transcriptor.commands.profile import cli as profile_cli


@pytest.fixture
def runner():
    return CliRunner()


class TestCli:
    def test_show_config(self, runner):
        result = runner.invoke(config_cli, ["show"])
        assert result.exit_code == 0
        assert "Date Format" in result.output
        assert "Base Dir" in result.output

    # TODO Handle configurations/environments better
    # Testing will change users configuration
    # def test_edit_config():
    #     runner = CliRunner()
    #     result = runner.invoke(config_cli, ['edit', '-b', ''])

    def test_show_profile(self, runner):
        result = runner.invoke(profile_cli, ["show"])
        assert result.exit_code == 0
        assert "First Name" in result.output
        assert "Last Name" in result.output
        assert "Area" in result.output
        assert "Country" in result.output

    # TODO Handle configurations/environments better
    # Testing will change users profile
    # def test_edit_config():
    #     runner = CliRunner()
    #     result = runner.invoke(profile_cli, ['edit', '-f', ''])

    def test_show_clients(self, runner):
        result = runner.invoke(clients_cli, ["list"])
        assert result.exit_code == 0
