import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy.exc import SQLAlchemyError

from transcriptor.database import Database


class TestDatabase(unittest.TestCase):
    @patch("transcriptor.database.Base.metadata.create_all")
    @patch("transcriptor.database.sqlite3.connect")
    def test_init_db_successful(self, mock_connect, mock_create_all):
        # Setup mock connection and metadata
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Initialize Database
        db = Database("test.db")

        # Test init_db
        db.init_db()

        # Assertions
        mock_connect.assert_called_once_with("test.db")
        mock_create_all.assert_called_once_with(mock_conn)

    @patch("transcriptor.database.Base.metadata.create_all")
    @patch("transcriptor.database.sqlite3.connect")
    def test_init_db_failure(self, mock_connect, mock_create_all):
        # Setup mock to raise an exception
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_create_all.side_effect = SQLAlchemyError("Error creating tables")

        # Initialize Database
        db = Database("test.db")

        # Test init_db
        with self.assertRaises(SQLAlchemyError):
            db.init_db()

        # Assertions
        mock_connect.assert_called_once_with("test.db")
        mock_create_all.assert_called_once_with(mock_conn)


if __name__ == "__main__":
    unittest.main()
