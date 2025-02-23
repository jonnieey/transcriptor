from .models import Base
import sqlite3


class Database:
    def __init__(self, db_file="sqlite:///:memory:"):
        self.db_file = db_file
        self.conn = sqlite3.connect(db_file)

    def init_db(self):
        Base.metadata.create_all(self.conn)
