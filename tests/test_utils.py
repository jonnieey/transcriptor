from transcriptor.utils import *


def test_parse_job_number():
    z = "2021-11-12-514779_DUE_11.15_(EXAMPLE)/514779 DUE 11.15 (EXAMPLE).zip"
    job_number = parse_job_number(z)
    assert job_number == "514779"


def test_parse_job_due_date():
    z = "2021-11-12-514779_DUE_11.15_(EXAMPLE)/514779 DUE 11.15 (EXAMPLE).zip"
    date_due = parse_due_date(z)
    assert date_due == "11.15"


def test_sec_to_min():
    s = 3630
    s2 = 3651
    m1 = sec_to_min(s)
    m2 = sec_to_min(s2)
    assert m1 == 60.5
    assert m2 == 60.85


def test_truncate():
    n = 45.67832
    assert truncate(n, 2) == 45.67


def test_format_date():
    rs = "11.15"
    date_fmt = "%Y-%m-%d"
    assert format_date(rs, date_fmt) == f"{date.today().year}-11-15"


def test_convert_cases():
    string = "this is me"
    assert sc(string) == "this_is_me"
    assert kc(string) == "this-is-me"
    assert tc(string) == "This Is Me"
    string2 = sc(string)
    assert tc(string2) == "This Is Me"
