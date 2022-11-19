from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base


class Database:
    def __init__(self, db_path="sqlite:///:memory:"):
        self.engine = create_engine(f"sqlite:///{db_path}", echo=True)
        self.session = Session(self.engine)


Base = declarative_base()
