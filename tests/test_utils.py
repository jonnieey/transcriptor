from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from transcriptor.date_utils import (
    date_to_str,
    extract_date_due,
    month_day_to_date,
    str_to_date,
)
from transcriptor.docx_utils import extract_table_data_from_docx
from transcriptor.filesystem import (
    get_media_files,
    mkdirp,
    next_non_existent_file,
    touch,
)
from transcriptor.invoice_utils import (
    html_to_md,
    md,
    render_invoice,
    render_summary_invoice,
    write_pdf,
)
from transcriptor.media_utils import (
    get_media_duration,
    round_up,
    seconds_to_minutes,
)
from transcriptor.sql_parsers import (
    parse_conditions,
    parse_conditions_as_dict,
    parse_sql_clause,
    parse_sql_update_query,
    type_convert,
)
from transcriptor.text_converters import (
    convert_case,
    extract_job_number,
    kc,
    nc,
    sc,
    tc,
)
from transcriptor.validators import (
    is_file,
    is_positive_number,
    is_valid_date,
    is_valid_job_type,
    is_valid_template,
    is_valid_yes_no,
)
from transcriptor.validators import template_mapping as TEMPLATE_MAPPING


# Test data and fixtures
@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path / "test_dir"


@pytest.fixture
def tmp_file(tmp_path):
    return tmp_path / "test_file.txt"


@pytest.fixture
def sample_invoice():
    class MockInvoice:
        pass

    invoice = MockInvoice()
    invoice.client_name = "Test Client"
    invoice.job_number = "123456"
    return invoice


@pytest.fixture
def sample_summary_invoice():
    class MockSummaryInvoice:
        pass

    invoice = MockSummaryInvoice()
    invoice.client_name = "Test Client"
    invoice.total_amount = 1000.00
    return invoice


# Test classes
class TestFileOperations:
    def test_touch_creates_file(self, tmp_file):
        touch([tmp_file])
        assert tmp_file.exists()

    def test_touch_creates_parent_dirs(self, tmp_dir):
        file_path = tmp_dir / "subdir" / "test.txt"
        touch([file_path])
        assert file_path.exists()

    def test_touch_multiple_files(self, tmp_dir):
        files = [tmp_dir / f"file_{i}.txt" for i in range(3)]
        touch(files)
        for f in files:
            assert f.exists()

    def test_mkdirp_creates_dirs(self, tmp_dir):
        dir_path = tmp_dir / "subdir" / "subsubdir"
        mkdirp([dir_path])
        assert dir_path.exists()
        assert dir_path.is_dir()


class TestStringOperations:
    @pytest.mark.parametrize(
        "input_str,from_,to_,expected",
        [
            ("hello-world", r"[ -]", "_", "hello_world"),
            ("hello_world", r"[_]", "-", "hello-world"),
            ("Hello World", r"\s", "", "HelloWorld"),
            ("", r"[ -]", "_", ""),  # Empty string
        ],
    )
    def test_convert_case(self, input_str, from_, to_, expected):
        assert convert_case(input_str, from_, to_) == expected

    def test_sc(self):
        assert sc("hello-world") == "hello_world"
        assert sc("hello world") == "hello_world"

    def test_nc(self):
        assert nc("hello_world") == "hello world"
        assert nc("hello-world") == "hello world"

    def test_kc(self):
        assert kc("hello world") == "hello-world"
        assert kc("hello_world") == "hello-world"

    def test_tc(self):
        assert tc("hello_world") == "Hello World"
        assert tc("hello-world") == "Hello World"


class TestDateOperations:
    @pytest.mark.parametrize(
        "date_str,date_fmt,expected",
        [
            ("12.31", "%m.%d", datetime(1900, 12, 31)),
            ("2023-12-31", "%Y-%m-%d", datetime(2023, 12, 31)),
            (datetime(2023, 12, 31), "%Y-%m-%d", datetime(2023, 12, 31)),
        ],
    )
    def test_str_to_date(self, date_str, date_fmt, expected):
        result = str_to_date(date_str, date_fmt)
        assert result == expected

    def test_str_to_date_invalid(self):
        with pytest.raises(ValueError):
            str_to_date("invalid", "%m.%d")

    @pytest.mark.parametrize(
        "date_obj,date_fmt,expected",
        [
            (datetime(2023, 12, 31), "%Y-%m-%d", "2023-12-31"),
            (date(2023, 12, 31), "%m/%d/%Y", "12/31/2023"),
        ],
    )
    def test_date_to_str(self, date_obj, date_fmt, expected):
        assert date_to_str(date_obj, date_fmt) == expected


class TestMediaOperations:
    @patch("transcriptor.filesystem.mimetypes.guess_type")
    def test_get_media_files(self, mock_guess, tmp_path):
        # Create a test file
        test_file = tmp_path / "test.mp3"
        test_file.touch()

        # Mock the mimetype guess to return audio type
        mock_guess.return_value = ("audio/mpeg", None)

        files = list(get_media_files(tmp_path))
        assert files == [test_file]

    @patch("transcriptor.media_utils.audio_open")
    def test_get_media_duration(self, mock_audio_open):
        mock_file = Path("test.mp3")
        mock_audio = mock_audio_open.return_value.__enter__.return_value
        mock_audio.duration = 125  # 2 minutes 5 seconds

        assert (
            get_media_duration(mock_file) == 2.5
        )  # Rounded up to nearest 0.5

    def test_seconds_to_minutes(self):
        assert seconds_to_minutes(60) == 1.0
        assert seconds_to_minutes(90) == 1.5
        assert seconds_to_minutes(95) == 2.0  # Rounds up

    def test_next_non_existent_file(self, tmp_file):
        touch([tmp_file])
        new_file = next_non_existent_file(tmp_file)
        assert new_file.name == "test_file_1.txt"
        assert not new_file.exists()


class TestNumberOperations:
    def test_round_up(self):
        assert round_up(1.0) == 1.0
        assert round_up(1.25) == 1.5
        assert round_up(1.5) == 1.5
        assert round_up(1.75) == 2.0

    def test_type_convert(self):
        assert type_convert("123") == 123
        assert type_convert("123.45") == 123.45
        assert type_convert("abc") == "abc"


class TestConditionParsing:
    def test_parse_conditions_as_dict(self):
        conditions = ["name=test", "id=1"]
        result = parse_conditions_as_dict(conditions)
        assert result == {"name": "test", "id": "1"}

    def test_parse_conditions(self):
        conditions = ["id<=1", "amount>0", "name~test"]
        result = parse_conditions(conditions)
        assert result == {
            "id": [("<=", 1)],
            "amount": [(">", 0)],
            "name": [("~", "test")],
        }

    def test_parse_conditions_mixed_types(self):
        conditions = ["id=1", "name=test", "amount=10.5"]
        result = parse_conditions(conditions)
        assert result["id"][0][1] == 1
        assert result["name"][0][1] == "test"
        assert result["amount"][0][1] == 10.5


class TestValidation:
    @patch("pathlib.Path.is_file")
    def test_is_file(self, mock_is_file):
        mock_is_file.return_value = True
        assert is_file("test.txt") is True
        mock_is_file.return_value = False
        assert is_file("nonexistent.txt") is False

    def test_is_positive_number(self):
        assert is_positive_number("123") is True
        assert is_positive_number("0") is False
        assert is_positive_number("-1") is False
        assert is_positive_number("abc") is False

    def test_is_valid_date(self):
        assert is_valid_date("2023-12-31") is True
        assert is_valid_date("12/31/2023") is True
        assert is_valid_date("invalid") is False

    def test_is_valid_yes_no(self):
        assert is_valid_yes_no("y") is True
        assert is_valid_yes_no("yes") is True
        assert is_valid_yes_no("n") is True
        assert is_valid_yes_no("no") is True
        assert is_valid_yes_no("maybe") is False

    def test_is_valid_job_type(self):
        assert is_valid_job_type("Normal") is True
        assert is_valid_job_type("Interpreted") is True
        assert is_valid_job_type("Expedite") is True
        assert is_valid_job_type("Invalid") is False

    def test_is_valid_template(self):
        for key in TEMPLATE_MAPPING:
            assert is_valid_template(key) is True
        assert is_valid_template("invalid") is False


class TestInvoiceRendering:
    @patch("transcriptor.invoice_utils._init_jinja_env")
    def test_render_invoice(self, mock_init, sample_invoice):
        mock_template = mock_init.return_value.get_template.return_value
        mock_template.render.return_value = "<html>test</html>"

        result = render_invoice(sample_invoice)
        assert result == "<html>test</html>"

    @patch("transcriptor.invoice_utils._init_jinja_env")
    def test_render_summary_invoice(self, mock_init, sample_summary_invoice):
        mock_template = mock_init.return_value.get_template.return_value
        mock_template.render.return_value = "<html>summary</html>"

        result = render_summary_invoice(sample_summary_invoice)
        assert result == "<html>summary</html>"

    @patch("transcriptor.invoice_utils.htmlstr_to_pdf")
    @patch("transcriptor.invoice_utils.render_invoice")
    def test_write_pdf(
        self, mock_render, mock_html_to_pdf, sample_invoice, tmp_file
    ):
        mock_render.return_value = "<html>test</html>"
        mock_html_to_pdf.return_value = b"pdf_content"

        result = write_pdf(sample_invoice, tmp_file, None)
        assert result == b"pdf_content"


class TestMarkdownConversion:
    def test_md_conversion(self):
        html = "<p>test</p>"
        result = md(html)
        assert result.strip() == "test"

    def test_html_to_md(self):
        html = (
            "<div><p>test</p><table><tr><td>content</td></tr></table></div>"
        )
        result = html_to_md(html)
        assert "content" in result


class TestDocxOperations:
    @patch("transcriptor.docx_utils.docx.Document")
    def test_extract_table_data_from_docx(self, mock_doc):
        # Create mock table structure
        mock_row = MagicMock()
        mock_cells = [MagicMock(text=f"cell_{i}") for i in range(3)]
        mock_row.cells = mock_cells

        mock_table = MagicMock()
        mock_table.rows = [mock_row]

        mock_doc_instance = MagicMock()
        mock_doc_instance.tables = [mock_table]
        mock_doc.return_value = mock_doc_instance

        result = extract_table_data_from_docx("test.docx")
        assert len(result) == 1
        assert result[0] == ["cell_0", "cell_1", "cell_2"]


class TestDateExtraction:
    def test_extract_job_number(self):
        assert extract_job_number("path/123456/file.txt") == "123456"
        assert extract_job_number("no_number_here") == ""

    def test_extract_date_due(self):
        assert extract_date_due("DUE_12-31") == "12-31"
        assert extract_date_due("BACK 12/31") == "12/31"
        assert extract_date_due("no_date_here") == ""

    def test_month_day_to_date(self):
        assert month_day_to_date("12.31") == f"{datetime.now().year}-12-31"
        assert month_day_to_date("12.31", year="2023") == "2023-12-31"
        assert month_day_to_date("invalid") == ""


class TestSQLParsing:
    def test_parse_sql_clause(self):
        clause = "name='test' AND id=1"
        result = parse_sql_clause(clause, "AND")
        assert result == {"name": "test", "id": "1"}

    def test_parse_sql_update_query(self):
        query = "SET amount=100 WHERE id=1 AND name='test'"
        set_assignments, where_assignments = parse_sql_update_query(query)
        assert set_assignments == {"amount": "100"}
        assert where_assignments == {"id": "1", "name": "test"}
