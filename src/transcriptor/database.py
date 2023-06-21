import sqlite3
from pathlib import Path


def dict_factory(cursor, row) -> dict:
    """
    Row factory for sqlite3. Converts a row to a dictionary.

    Arguments:
        cursor: sqlite3 cursor
        row: sqlite3 row

    Returns:
        A dictionary
    """
    fields = [column[0] for column in cursor.description]
    return dict(zip(fields, row))


class Database:
    def __init__(self, db_file="sqlite:///:memory:"):
        self.db_file = db_file

        # Detect types by columns and declaration
        self.conn = sqlite3.connect(
            db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )

        self.conn.row_factory = dict_factory

    def init_db(self):
        """
        Initialize the database

        Returns:
            sqlite3 connection
        """
        init_sql = Path(__file__).parent.joinpath("createdb.sql")
        with open(init_sql, "r") as fd:
            self.conn.executescript(fd.read())
        self.conn.commit()
        return self.conn
