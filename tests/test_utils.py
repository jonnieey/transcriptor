from datetime import date

from transcriptor.utils import (
    date_to_string,
    get_config,
    get_quantity,
    parse_job_due_date,
    parse_job_number,
    sec_to_min,
    string_to_date,
)

DATE_FMT = get_config()["date_fmt"]


def test_date_to_string():
    date_obj = date.today()
    date_string = date_to_string(date_obj)
    assert date_obj.strftime(DATE_FMT) == date_string


def test_string_to_date():
    today = date.today()
    date_obj = string_to_date(today.strftime(DATE_FMT))
    assert date_obj == today


def test_parse_job_number():
    zip = "2021-11-12-514779_DUE_11.15_(EXAMPLE)/514779 DUE 11.15 (EXAMPLE).zip"
    job_number = parse_job_number(zip)
    assert job_number == "514779"


def test_parse_job_due_date():
    zip = "2021-11-12-514779_DUE_11.15_(EXAMPLE)/514779 DUE 11.15 (EXAMPLE).zip"
    date_due = parse_job_due_date(zip)
    d = "%s-11-15" % (date.today().year)
    assert date_due == d


def test_sec_to_min():
    seconds = 3600
    min = sec_to_min(seconds)
    assert min == 60


def test_get_quantity_as_int():
    inp = "23"
    q = get_quantity(inp, total_q=46)
    assert q == 23


def test_get_quantity_as_fraction():
    fraction = "1/5"
    q = get_quantity(fraction, 50)
    assert q == 10


def test_get_quantity_as_word():
    # only accepts whole, half, quarter
    word = "half"
    q = get_quantity(word, 50)
    assert q == 25
