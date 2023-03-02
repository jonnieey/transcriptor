import tempfile
import unittest
from pathlib import Path

from transcriptor.models import ConfigModel, ProfileModel


class TestConfigModel(unittest.TestCase):
    def test_ConfigModel(self):
        # Test setting and getting attributes
        config = ConfigModel(date_format="%Y-%m-%d", base_dir="/home/user")
        self.assertEqual(config.get("date_format"), "%Y-%m-%d")
        self.assertEqual(config.get("base_dir"), "/home/user")
        config.set("base_dir", "/mnt/data")
        self.assertEqual(config.get("base_dir"), "/mnt/data")

        # Test saving and loading from a file
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            config.save(f)
            f.seek(0)
            loaded_config = ConfigModel().from_file(f.name)
            self.assertEqual(loaded_config.get("date_format"), "%Y-%m-%d")
            self.assertEqual(loaded_config.get("base_dir"), "/mnt/data")

        # Test loading from environment variables
        dev_config = ConfigModel().from_env("dev")
        self.assertEqual(
            dev_config.get("base_dir"),
            str(Path(__file__).parent.parent.joinpath("dev-dir")),
        )


class TestProfileModel(unittest.TestCase):
    def test_ProfileModel(self):
        # Test setting and getting attributes
        profile = ProfileModel(
            first_name="first_name",
            last_name="last_name",
            area="area",
            country="country",
        )
        self.assertEqual(profile.get("first_name"), "first_name")
        self.assertEqual(profile.get("last_name"), "last_name")
        self.assertEqual(profile.get("area"), "area")
        self.assertEqual(profile.get("country"), "country")
        profile.set("area", "my area")
        self.assertEqual(profile.get("area"), "my area")

        # Test saving and loading from a file
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            profile.save(f)
            f.seek(0)
            loaded_profile = ProfileModel().from_file(f.name)
            self.assertEqual(loaded_profile.get("area"), "my area")
            self.assertEqual(loaded_profile.get("first_name"), "first_name")
