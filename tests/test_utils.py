import pytest

from transcriptor.utils import *


def test_touch(base_dir):
    file_1 = base_dir.joinpath("some_dir").joinpath("test_file.yml")
    touch([file_1])
    assert file_1.exists() is True
    assert base_dir.joinpath("some_dir").exists() is True
    assert base_dir.joinpath("some_dir").is_dir() is True
    file_1.unlink()
    base_dir.joinpath("some_dir").rmdir()


def test_mkdirp(base_dir):
    dir_1 = base_dir.joinpath("test_dir").joinpath("files")
    mkdirp([dir_1])
    assert dir_1.exists()
    assert dir_1.is_dir()
    assert dir_1.parent.name == "test_dir"
    dir_1.rmdir()
    dir_1.parent.rmdir()


def test_convert_cases():
    string = "My Name"
    assert convert_case(string, " ", "_") == "My_Name"


def test_sc():
    string = "My Name"
    assert sc(string) == "My_Name"


def test_nc():
    string = "My_Name"
    assert nc(string) == "My Name"


def test_kc():
    string = "My Name"
    assert kc(string) == "My-Name"


def test_tc():
    string = "my name"
    assert tc(string) == "My Name"


def test_parse_job_number():
    z = "2021-11-12-514779_DUE_11.15_(EXAMPLE)/514779 DUE 11.15 (EXAMPLE).zip"
    job_number = parse_job_number(z)
    assert job_number == "514779"


def test_parse_due_date():
    z = "2021-11-12-514779_DUE_11.15_(EXAMPLE)/514779 DUE 11.15 (EXAMPLE).zip"
    date_due = parse_due_date(z)
    assert date_due == "11.15"


def test_truncate():
    n = 45.67832
    assert truncate(n, 2) == 45.67
    assert truncate(n, 3) == 45.678
    assert truncate(n, 0) == 45.0


def test_sec_to_min():
    s = 3630
    s2 = 3651
    m1 = sec_to_min(s)
    m2 = sec_to_min(s2)
    assert m1 == 60.5
    assert m2 == 60.85


def test_format_date():
    rs = "11.15"
    date_fmt = "%Y-%m-%d"
    assert format_date(rs, date_fmt) == f"{date.today().year}-11-15"


def test_str_to_date():
    assert isinstance(str_to_date("2023-01-01", "%Y-%m-%d"), datetime)
    assert isinstance(std("2023-01-01", "%Y-%m-%d"), datetime)


def test_date_to_str():
    assert isinstance(date_to_str(datetime.today(), "%Y-%m-%d"), str)
    assert isinstance(dts(datetime.today(), "%Y-%m-%d"), str)


def test_parse_quantity():
    quantity = 50
    total_quantity = 100
    assert parse_quantity(quantity, total_quantity) == 50.0
    quantity = "50"
    assert parse_quantity(quantity, total_quantity) == 50.0
    quantity = "1/2"
    assert parse_quantity(quantity, total_quantity) == 50.0
    quantity = "0.5"
    assert parse_quantity(quantity, total_quantity) == 50.0


def test_rel_date():
    assert rel_date(2).strftime("%x") == (
        datetime.today() + timedelta(days=2)
    ).strftime("%x")
