#!/usr/bin/python3
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

from transcriptor.base import Transcriptor
from transcriptor.cli2 import TranscriptorCMD
from transcriptor.models import ConfigModel


class TestCMD:
    def setup_class(self):
        self.temp_dir = tempfile.mkdtemp()
        CONFIG = {"date_format": "%Y-%m-%d", "base_dir": f"{self.temp_dir}"}
        self.config = ConfigModel(**CONFIG)

    def setup_method(self):
        self.app = Transcriptor(config=self.config)
        self.cmd = TranscriptorCMD(app=self.app)
        # setattr(self.cmd, "app", self.app)
        # print(dir(self.cmd))

    # def test_print_help(self):
    # with mock.patch("sys.stdout", new=StringIO()) as fake_out:
    # with mock.patch("sys.stdout", new=StringIO()) as fake_out:
    # # print(self.cmd.app.config)
    # self.cmd.onecmd("help")
    # assert "Documented commands" in fake_out.getvalue()
    # assert "base_dir" in fake_out.getvalue()

    def test_prompt(self):
        assert self.cmd.prompt == "(trans) "

    def test_config(self):
        # show config
        with mock.patch("sys.stdout", new=StringIO()) as fake_out:
            self.cmd.onecmd("show config")
            assert "Date Format" in fake_out.getvalue()
            assert "Base Dir" in fake_out.getvalue()
            assert f"{self.temp_dir}" in fake_out.getvalue()

        # update config
        with mock.patch("sys.stdout", new=StringIO()) as fake_out:
            self.cmd.onecmd(
                f"update config base-dir {Path(self.temp_dir).joinpath('test')}"
            )
            self.cmd.onecmd("update config date-format %Y-%d-%m")
            self.cmd.onecmd("show config")
            assert "%Y-%d-%m" in fake_out.getvalue()
            assert f"{Path(self.temp_dir).joinpath('test')}" in fake_out.getvalue()

    def test_profile(self):
        # show profile
        with mock.patch("sys.stdout", new=StringIO()) as fake_out:
            self.cmd.onecmd("show profile")
            assert "Area" in fake_out.getvalue()
            assert "First Name" in fake_out.getvalue()
            assert "Last Name" in fake_out.getvalue()
            assert "Country" in fake_out.getvalue()

        # update profile
        with mock.patch("sys.stdout", new=StringIO()) as fake_out:
            self.cmd.onecmd("update profile first-name 'John'")
            self.cmd.onecmd("update profile last-name 'Doe'")
            self.cmd.onecmd("update profile country 'USA'")
            self.cmd.onecmd("show profile")
            assert "John" in fake_out.getvalue()
            assert "Doe" in fake_out.getvalue()
            assert "USA" in fake_out.getvalue()

    # def test_client_add(self):
    #     # add client
    #     with mock.patch("sys.stdout", new=StringIO()) as fake_out:
    #         self.cmd.onecmd("add client first-name 'John'")
    #         self.cmd.onecmd("add client last-name 'Doe'")
    #         self.cmd.onecmd("add client country 'USA'")
    #         self.cmd.onecmd("show clients")
    #         assert "John" in fake_out.getvalue()
    #         assert "Doe" in fake_out.getvalue()
    #         assert "USA" in fake_out.getvalue()
    # #
    # # def tests_update_client(self):
    # #     # update client
    # #     with mock.patch("sys.stdout", new=StringIO()) as fake_out:
    # #         self.cmd().onecmd("update client first-name 'John'")
    # #         self.cmd().onecmd("update client last-name 'Doe'")
    # #         self.cmd().onecmd("update client country 'USA'")
    # #         self.cmd().onecmd("show clients")
    # #         assert "John" in fake_out.getvalue()
    # #         assert "Doe" in fake_out.getvalue()
    # #         assert "USA" in fake_out.getvalue()
