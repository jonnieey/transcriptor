from .models import Base

from sqlalchemy import create_engine
from sqlalchemy import event


class Database:
    def __init__(self, db_file=":memory:"):
        self.db_file = db_file

        self.engine = create_engine(f"sqlite:///{db_file}", echo=True)

        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    def init_db(self):
        Base.metadata.create_all(self.engine)
