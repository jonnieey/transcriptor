from .models import Base

from sqlalchemy import create_engine


class Database:
    def __init__(self, db_file="sqlite:///:memory:"):
        self.db_file = db_file

        self.engine = create_engine(f"sqlite:///{db_file}")

    def init_db(self):
        Base.metadata.create_all(self.engine)
