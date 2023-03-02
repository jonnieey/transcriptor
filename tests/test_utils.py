import mimetypes
import os
import tempfile
import unittest
import unittest.mock
from datetime import date, datetime, timedelta
from pathlib import Path

from transcriptor.utils import (
    convert_case,
    date_to_str,
    dts,
    format_date,
    get_media_duration,
    get_media_files,
    is_valid_date,
    is_valid_email,
    is_valid_string,
    is_valid_yes_no,
    kc,
    list_of_rows_to_csv,
    mkdirp,
    nc,
    parse_due_date,
    parse_job_number,
    parse_quantity,
    rel_date,
    sc,
    sec_to_min,
    std,
    str_to_date,
    touch,
    truncate,
)


class TestTouch(unittest.TestCase):
    def test_touch_creates_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.txt")
            touch([file_path])
            self.assertTrue(os.path.isfile(file_path))

    def test_touch_creates_multiple_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_paths = [
                os.path.join(temp_dir, "test1.txt"),
                os.path.join(temp_dir, "test2.txt"),
            ]
            touch(file_paths)
            self.assertTrue(os.path.isfile(file_paths[0]))
            self.assertTrue(os.path.isfile(file_paths[1]))

    def test_touch_does_not_create_file_if_it_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.txt")
            open(file_path, "w").close()
            touch([file_path])
            self.assertTrue(os.path.isfile(file_path))

    def test_touch_creates_file_with_parents(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = os.path.join(temp_dir, "subdir")
            file_path = os.path.join(dir_path, "test.txt")
            touch([file_path])
            self.assertTrue(os.path.isdir(dir_path))
            self.assertTrue(os.path.isfile(file_path))

    def test_touch_creates_file_with_given_permissions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.txt")
            touch([file_path])
            self.assertEqual(os.stat(file_path).st_mode & 0o777, 0o644)
            os.chmod(file_path, 0o600)
            touch([file_path])
            self.assertEqual(os.stat(file_path).st_mode & 0o777, 0o600)


class TestMkdirp(unittest.TestCase):
    def test_mkdirp(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested directories to test mkdirp
            dir_paths = [Path(temp_dir) / "foo/bar/baz", Path(temp_dir) / "qux"]
            mkdirp(dir_paths)

            # Check if the directories were created
            self.assertTrue(dir_paths[0].is_dir())
            self.assertTrue(dir_paths[1].is_dir())

            # Check if the parent directories were created as well
            self.assertTrue((Path(temp_dir) / "foo").is_dir())
            self.assertTrue((Path(temp_dir) / "foo/bar").is_dir())

            # Check if mkdirp can handle existing directories
            mkdirp(dir_paths)
            self.assertTrue(dir_paths[0].is_dir())

            # Check if mkdirp can handle Path objects as input
            path_dirs = [
                Path(temp_dir) / "path_foo/path_bar",
                Path(temp_dir) / "path_qux",
            ]
            mkdirp(path_dirs)
            self.assertTrue(path_dirs[0].is_dir())
            self.assertTrue(path_dirs[1].is_dir())


class TestConvertCase(unittest.TestCase):
    def test_convert_case(self):

        self.assertEqual(convert_case("My Name", " ", "_"), "My_Name")
        self.assertEqual(sc("My Name"), "My_Name")
        self.assertEqual(sc("My-Name"), "My_Name")
        self.assertEqual(nc("My_Name"), "My Name")
        self.assertEqual(nc("My-Name"), "My Name")
        self.assertEqual(kc("My Name"), "My-Name")
        self.assertEqual(kc("My_Name"), "My-Name")


class TestParseJobNumber(unittest.TestCase):
    def test_parse_job_number_with_valid_job_number(self):
        file_path = "/path/to/534223-file.txt"
        self.assertEqual(parse_job_number(file_path), "534223")

    def test_parse_job_number_with_multiple_job_numbers(self):
        file_path = "/path/to/123456-534223-file.txt"
        self.assertEqual(parse_job_number(file_path), "123456")

    def test_parse_job_number_with_no_job_number(self):
        file_path = "/path/to/file.txt"
        self.assertEqual(parse_job_number(file_path), "")

    def test_parse_job_number_with_shorter_job_number(self):
        file_path = "/path/to/123-file.txt"
        self.assertEqual(parse_job_number(file_path), "")

    def test_parse_job_number_with_longer_job_number(self):
        file_path = "/path/to/123456789-file.txt"
        self.assertEqual(parse_job_number(file_path), "")


class TestDateParses(unittest.TestCase):
    def test_parse_due_date(self):
        self.assertEqual(parse_due_date("file_due_12.24.txt"), "12.24")
        self.assertEqual(parse_due_date("file-back_02.14.pdf"), "02.14")
        self.assertEqual(parse_due_date("file_due-8-9.txt"), "8-9")
        self.assertEqual(parse_due_date("file_due 05-06.txt"), "05-06")
        self.assertEqual(parse_due_date("file_due-01-31.xlsx"), "01-31")
        self.assertEqual(parse_due_date("file_no_date.txt"), "")

    def test_format_date(self):
        assert format_date("02.29", "%Y-%m-%d") == ""  # invalid date
        assert (
            format_date("01.01", "%Y-%m-%d") == f"{datetime.now().year}-01-01"
        )  # current year
        assert (
            format_date("12.25", "%B %d, %Y") == f"December 25, {datetime.now().year}"
        )  # current year

    def test_str_to_date(self):
        self.assertIsInstance(str_to_date("2023-01-01", "%Y-%m-%d"), datetime)
        self.assertIsInstance(std("2023-01-01", "%Y-%m-%d"), datetime)
        self.assertEqual(std("2023-01-01", "%Y-%m-%d").year, 2023)

    def test_date_to_str(self):
        d = std("2023-01-01", "%Y-%m-%d")
        self.assertIsInstance(date_to_str(d, "%Y-%m-%d"), str)
        self.assertIsInstance(dts(d, "%Y-%m-%d"), str)
        self.assertEqual(dts(d, "%Y-%m-%d"), "2023-01-01")


class TestGetMediaFiles(unittest.TestCase):
    def test_returns_list(self):
        directory = Path(__file__).parent.joinpath("media_files")
        media_files = get_media_files(directory)
        self.assertIsInstance(media_files, list)

    def test_returns_only_media_files(self):
        directory = Path(__file__).parent.joinpath("media_files")
        media_files = get_media_files(directory)
        for file in media_files:
            mime_type, _ = mimetypes.guess_type(str(file))
            # print(file, mime_type, _)
            self.assertTrue(
                mime_type.startswith("audio/")
                or mime_type.startswith("video/")
                or mime_type == "application/octet-stream"
            )

    def test_returns_sorted_list(self):
        directory = Path(__file__).parent.joinpath("media_files")
        media_files = get_media_files(directory)
        sorted_files = sorted(media_files)
        self.assertEqual(media_files, sorted_files)


class TestGetMediaFilesDuration(unittest.TestCase):
    def test_returns_float(self):
        directory = Path(__file__).parent.joinpath("media_files")
        media_files = get_media_files(directory)
        for media_file in media_files:
            self.assertIsInstance(get_media_duration(media_file), float)

    def test_get_media_duration(self):
        directory = Path(__file__).parent.joinpath("media_files")
        media_file = directory.joinpath("Sample.aac")
        duration_in_sec = 16.1
        expected_duration_in_min = 0.26
        # create a mock object with a duration attribute
        class MockAudioFile:
            duration = duration_in_sec

        # mock the audio_open function to return the mock object
        with unittest.mock.patch("audioread.audio_open", return_value=MockAudioFile()):
            duration_in_min = get_media_duration(media_file)
        self.assertEqual(duration_in_min, expected_duration_in_min)


class TestMathOperations(unittest.TestCase):
    def test_truncate(self):
        # Test case 1: Truncate a positive number to 2 decimal places

        self.assertEqual(truncate(3.14159, 2), 3.14)

        # Test case 2: Truncate a negative number to 3 decimal places
        self.assertEqual(truncate(-2.71828, 3), -2.718)

        # Test case 3: Truncate a number with no decimal places to 4 decimal places
        self.assertEqual(truncate(100, 4), 100.0000)

        # Test case 4: Truncate a number with more decimal places than specified
        self.assertEqual(truncate(0.123456789, 4), 0.1234)

        # Test case 5: Truncate a number with exactly the same number of decimal places as specified
        self.assertEqual(truncate(5.6789, 4), 5.6789)

        # Test case 6: Truncate a number to 0 decimal places
        self.assertEqual(truncate(9.87654, 0), 9.0)

        # Test case 7: Truncate a number to 1 decimal place
        self.assertEqual(truncate(1.2345, 1), 1.2)

        # Test case 8: Truncate a number to 5 decimal places
        self.assertEqual(truncate(1234.56789, 5), 1234.56789)

        # Test case 9: Truncate a number to a negative number of decimal places
        self.assertEqual(truncate(99.999, -1), 90.0)

        # Test case 10: Truncate a number to a large number of decimal places
        self.assertEqual(truncate(1.1, 10), 1.1)

        # Test case 11: Truncate zero to any number of decimal places
        self.assertEqual(truncate(0, 5), 0.00000)
        self.assertEqual(truncate(0, 0), 0.0)

    def test_sec_to_min(self):
        # Test case 1: Convert 60 seconds to 1 minute
        self.assertEqual(sec_to_min(60), 1.0)

        # Test case 2: Convert 120 seconds to 2 minutes
        self.assertEqual(sec_to_min(120), 2.0)

        # Test case 3: Convert 30 seconds to 0.5 minutes
        self.assertEqual(sec_to_min(30), 0.5)

        # Test case 4: Convert 90 seconds to 1.5 minutes
        self.assertEqual(sec_to_min(90), 1.5)

        # Test case 5: Convert 75 seconds to 1.25 minutes
        self.assertEqual(sec_to_min(75), 1.25)

        # Test case 6: Convert 0 seconds to 0 minutes
        self.assertEqual(sec_to_min(0), 0.0)

        # Test case 7: Convert a decimal number of seconds to minutes
        self.assertEqual(sec_to_min(3600.5), 60.00)

        # Test case 8: Convert a negative number of seconds to minutes
        self.assertEqual(sec_to_min(-180), -3.0)

        # Test case 9: Convert a large number of seconds to minutes
        self.assertEqual(sec_to_min(86400), 1440.0)

    def test_parse_quantity(self):
        # Test case 1: Valid float quantity
        self.assertEqual(parse_quantity(3.1415, None), 3.14)

        # Test case 2: Valid integer quantity
        self.assertEqual(parse_quantity(10, None), 10.0)

        # Test case 3: Valid fraction quantity
        self.assertEqual(parse_quantity("1/2", 10), 5.0)

        # Test case 4: Invalid fraction quantity (less than 1) with missing total quantity
        try:
            parse_quantity("1/4", None)
            self.assertFalse("Expected TypeError for missing total quantity")
        except TypeError:
            pass

        # Test case 5: Invalid fraction quantity (less than 1) with valid total quantity
        self.assertEqual(parse_quantity("1/3", 9), 3.0)

        # Test case 6: Invalid fraction quantity (greater than 1)
        try:
            parse_quantity("2/1", None)
            self.assertFalse("Expected TypeError for invalid fraction quantity")
        except TypeError:
            pass

        # Test case 7: Invalid string input
        try:
            parse_quantity("not a valid input", None)
            self.assertFalse("Expected TypeError for invalid input")
        except TypeError:
            pass

        # Test case 8: Invalid input type (list)
        try:
            parse_quantity([1, 2, 3], None)
            self.assertFalse("Expected TypeError for invalid input type")
        except TypeError:
            pass


class TestObjectsToCSV(unittest.TestCase):
    def test_list_of_rows_to_csv_with_headers_and_omit(self):
        class Row:
            def __init__(self, col1, col2, col3):
                self.col1 = col1
                self.col2 = col2
                self.col3 = col3

        rows = [Row(1, 2, 3), Row(4, 5, 6), Row(7, 8, 9)]

        headers = ["col2", "col3"]
        omit = ["col1"]

        expected_output = "col2,col3\r\n2,3\r\n5,6\r\n8,9\r\n"

        self.assertEqual(list_of_rows_to_csv(rows, headers, omit), expected_output)

    def test_list_of_rows_to_csv_with_headers_no_omit(self):
        class Row:
            def __init__(self, col1, col2, col3):
                self.col1 = col1
                self.col2 = col2
                self.col3 = col3

        rows = [Row(1, 2, 3), Row(4, 5, 6), Row(7, 8, 9)]

        headers = ["col1", "col2", "col3"]

        expected_output = "col1,col2,col3\r\n1,2,3\r\n4,5,6\r\n7,8,9\r\n"

        self.assertEqual(list_of_rows_to_csv(rows, headers), expected_output)

    def test_list_of_rows_to_csv_no_headers_no_omit(self):
        class Row:
            def __init__(self, col1, col2, col3):
                self.col1 = col1
                self.col2 = col2
                self.col3 = col3

        rows = [Row(1, 2, 3), Row(4, 5, 6), Row(7, 8, 9)]

        expected_output = "1,2,3\r\n4,5,6\r\n7,8,9\r\n"

        self.assertEqual(list_of_rows_to_csv(rows), expected_output)

    def test_list_of_rows_to_csv_with_empty_rows(self):
        class Row:
            def __init__(self, col1, col2, col3):
                self.col1 = col1
                self.col2 = col2
                self.col3 = col3

        rows = []

        expected_output = ""

        self.assertEqual(list_of_rows_to_csv(rows), expected_output)

    def test_list_of_rows_to_csv_with_empty_headers(self):
        class Row:
            def __init__(self, col1, col2, col3):
                self.col1 = col1
                self.col2 = col2
                self.col3 = col3

        rows = [Row(1, 2, 3), Row(4, 5, 6), Row(7, 8, 9)]

        headers = []

        expected_output = "1,2,3\r\n4,5,6\r\n7,8,9\r\n"

        self.assertEqual(list_of_rows_to_csv(rows, headers), expected_output)


class TestRelativeDate(unittest.TestCase):
    def test_rel_date(self):
        # Test that the function returns a date object
        self.assertIsInstance(rel_date(0), date)

        # Test that the function returns the correct date for positive values
        today = datetime.today().date()
        self.assertEqual(rel_date(1), today + timedelta(days=1))
        self.assertEqual(rel_date(10), today + timedelta(days=10))
        self.assertEqual(rel_date(365), today + timedelta(days=365))

        # Test that the function returns the correct date for negative values
        self.assertEqual(rel_date(-1), today - timedelta(days=1))
        self.assertEqual(rel_date(-10), today - timedelta(days=10))
        self.assertEqual(rel_date(-365), today - timedelta(days=365))


class TestValidatorFunctions(unittest.TestCase):
    def test_is_valid_email(self):
        # Test that the function returns True for valid email addresses
        self.assertTrue(is_valid_email("example@gmail.com"))
        self.assertTrue(is_valid_email("john.doe@example.com"))
        self.assertTrue(is_valid_email("john+doe@example.co.uk"))
        self.assertTrue(is_valid_email("jane_doe123@example.com"))

        # Test that the function returns False for invalid email addresses
        self.assertFalse(is_valid_email("example.com"))
        self.assertFalse(is_valid_email("example@com"))
        self.assertFalse(is_valid_email("example@.com"))
        self.assertFalse(is_valid_email("example@com."))
        self.assertFalse(is_valid_email("example@com.."))
        # assert is_valid_email("example@com-.com") == False
        self.assertFalse(is_valid_email("example@com_.com"))

    def test_is_valid_string(self):
        self.assertTrue(is_valid_string("test"))
        self.assertTrue(is_valid_string("0test"))
        self.assertTrue(is_valid_string("0-test2"))
        self.assertFalse(is_valid_string(""))
        self.assertFalse(is_valid_string(None))

    def test_is_valid_yes_no(self):
        self.assertTrue(is_valid_yes_no("yes"))
        self.assertTrue(is_valid_yes_no("YES"))
        self.assertTrue(is_valid_yes_no("yES"))
        self.assertTrue(is_valid_yes_no("y"))
        self.assertTrue(is_valid_yes_no("Y"))
        self.assertTrue(is_valid_yes_no("n"))
        self.assertTrue(is_valid_yes_no("N"))
        self.assertTrue(is_valid_yes_no("no"))
        self.assertTrue(is_valid_yes_no("NO"))
        self.assertTrue(is_valid_yes_no("nO"))
        self.assertTrue(is_valid_yes_no("nO"))
        self.assertFalse(is_valid_yes_no("0"))

    def test_is_valid_date(self):
        self.assertIsInstance(is_valid_date("01/01/2020"), bool)
        self.assertTrue(is_valid_date("01/01/2020"))
        self.assertFalse(is_valid_date("01/01/20"))
        self.assertTrue(is_valid_date("01-01-2020"))
        self.assertFalse(is_valid_date("01-01-20"))
        self.assertTrue(is_valid_date("01.01.2020"))
        self.assertFalse(is_valid_date("01.01.20"))
