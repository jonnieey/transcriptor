import unittest

from transcriptor.models import ConfigModel, ProfileModel


class TestConfigModel(unittest.TestCase):
    def test_ConfigModel(self):
        # Test setting and getting attributes
        config = ConfigModel(date_format="%Y-%m-%d", base_dir="/home/user")
        self.assertEqual(config.get("date_format"), "%Y-%m-%d")
        self.assertEqual(config.get("base_dir"), "/home/user")
        config.set("base_dir", "/mnt/data")
        self.assertEqual(config.get("base_dir"), "/mnt/data")


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
