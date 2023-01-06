from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base


class Database:
    def __init__(self, db_path="sqlite:///:memory:"):
        self.engine = create_engine(f"sqlite:///{db_path}")


Base = declarative_base()
