from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

from transcriptor.view import TranscriptorView


@pytest.fixture
def view():
    return TranscriptorView()


class TestViewGeneration:
    def test_generate_table_vertical_dict(self, view):
        data = {"key1": "value1", "key2": "value2"}
        view.generate_table(data, orientation="vertical")

        # Access the private table attribute to verify structure
        assert len(view.table.columns) == 2
        assert view.table.columns[0].header == "Option"
        assert view.table.columns[1].header == "Value"

    def test_generate_table_horizontal_list_of_dicts(self, view):
        data = [
            {"id": 1, "name": "Item 1", "amount": 10.0},
            {"id": 2, "name": "Item 2", "amount": 20.0},
        ]
        view.generate_table(data, orientation="horizontal")

        assert len(view.table.columns) == 3
        headers = [c.header for c in view.table.columns]
        assert "Id" in headers
        assert "Name" in headers
        assert "Amount" in headers

    def test_generate_table_horizontal_list_of_lists(self, view):
        data = [
            ["Header1", "Header2"],
            ["Val1", "Val2"],
            ["Val3", "Val4"],
        ]
        view.generate_table(data, orientation="horizontal")

        assert len(view.table.columns) == 2
        headers = [c.header for c in view.table.columns]
        assert "Header1" in headers
        assert "Header2" in headers

    def test_generate_table_with_ordination(self, view):
        data = {"key1": "value1", "key2": "value2"}
        view.generate_table(data, orientation="vertical", ordination=["key2"])

    def test_empty_data(self, view):
        view.generate_table([])
        assert len(view.table.columns) == 0


class TestItemStyle:
    def test_submitted_paid_less(self, view):
        item = {
            "date_submitted": "2023-01-01",
            "amount": 100.0,
            "amount_paid": 50.0,
        }
        style = view._get_item_style(item)
        assert style == "#8be9fd"

    def test_submitted_paid_full(self, view):
        item = {
            "date_submitted": "2023-01-01",
            "amount": 100.0,
            "amount_paid": 100.0,
        }
        style = view._get_item_style(item)
        assert style == "#f8f8f2"

    def test_due_date_passed(self, view):
        past_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        item = {"date_due": past_date}
        style = view._get_item_style(item)
        assert style == "#bd93f9"

    def test_due_date_imminent(self, view):
        # 1 day left
        soon_date = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        item = {"date_due": soon_date}
        style = view._get_item_style(item)
        assert style == "#ff5555"

    def test_due_date_soon(self, view):
        # 3 days left
        soon_date = (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")
        item = {"date_due": soon_date}
        style = view._get_item_style(item)
        assert style == "#f1fa8c"

    def test_due_date_far(self, view):
        # 10 days left
        far_date = (date.today() + timedelta(days=10)).strftime("%Y-%m-%d")
        item = {"date_due": far_date}
        style = view._get_item_style(item)
        assert style == "#50fa7b"

    def test_invalid_date(self, view):
        item = {"date_due": "invalid-date"}
        style = view._get_item_style(item)
        assert style == "#f8f8f2"

    def test_default_style(self, view):
        item = {"other": "value"}
        style = view._get_item_style(item)
        assert style == "#f8f8f2"


class TestPrintTable:
    def test_print_table(self, view):
        # Mock console to verify print called
        view.console = MagicMock()
        data = {"key": "value"}
        view.print_table(data)
        view.console.print.assert_called_once()
