from sqlalchemy import create_engine, event

from .models import Base


class Database:
    def __init__(self, db_file: str = ":memory:"):
        self.db_file = db_file

        self.engine = create_engine(f"sqlite:///{db_file}")

        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record: str):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    def init_db(self):
        Base.metadata.create_all(self.engine)
