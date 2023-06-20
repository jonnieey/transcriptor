# from sqlalchemy import create_engine
# from sqlalchemy.orm import declarative_base
#
#
# class Database:
#     def __init__(self, db_path="sqlite:///:memory:"):
#         self.engine = create_engine(f"sqlite:///{db_path}", echo=True)
#
#
# Base = declarative_base()
import sqlite3
from pathlib import Path


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return dict(zip(fields, row))


class Database:
    def __init__(self, db_file="sqlite:///:memory:"):
        self.db_file = db_file
        self.conn = sqlite3.connect(
            db_file, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )

        # provide indexed and case-insensitive named access to columns
        self.conn.row_factory = dict_factory

    def init_db(self):
        init_sql = Path(__file__).parent.joinpath("createdb.sql")
        with open(init_sql, "r") as fd:
            self.conn.executescript(fd.read())
        self.conn.commit()
        return self.conn
