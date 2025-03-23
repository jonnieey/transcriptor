import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from transcriptor.utils import (
    get_media_files,
    kc,
    mkdirp,
    nc,
    next_non_existent_file,
    sc,
    str_to_date,
    tc,
    touch,
)


@pytest.fixture
def temp_dir():
    dir_path = tempfile.mkdtemp()
    yield Path(dir_path)
    shutil.rmtree(dir_path)


def test_touch(temp_dir):
    # List to hold file paths
    file1 = temp_dir / "subdir/test1.txt"
    file2 = temp_dir / "subdir/test2.txt"
    touch([file1, file2])

    # Check presence of files and directories
    assert file1.exists()
    assert file2.exists()
    assert file1.parent.exists()


def test_mkdirp(temp_dir):
    dir1 = temp_dir / "testdir1/subdir"
    dir2 = temp_dir / "testdir2"
    mkdirp([dir1, dir2])

    assert dir1.exists()
    assert dir2.exists()


def test_convert_case_functions():
    assert sc("test-string") == "test_string"
    assert nc("test-string_test") == "test string test"
    assert kc("test string") == "test-string"
    assert tc("test-string_test") == "Test String Test"


def test_str_to_date():
    date_string = "12.25"
    date_fmt = "%m.%d"
    result = str_to_date(date_string, date_fmt)
    assert isinstance(result, datetime)
    assert result.month == 12
    assert result.day == 25


def test_get_media_files(temp_dir):
    # Create some temporary files
    media_file = temp_dir / "video.mp4"
    non_media_file = temp_dir / "document.txt"
    touch([media_file, non_media_file])

    media_file_list = list(get_media_files(temp_dir))
    assert media_file in media_file_list
    assert non_media_file not in media_file_list


def test_next_non_existent_file(temp_dir):
    filename = temp_dir / "test.txt"
    touch([filename])  # Create the file

    next_file = next_non_existent_file(str(filename))
    assert str(next_file) == str(temp_dir / "test_1.txt")
