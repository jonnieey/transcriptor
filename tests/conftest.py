from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from transcriptor.database import Base, Database
from transcriptor.utils import *

BASE_DIR = Path(__file__).parent.joinpath("data")
mkdirp([BASE_DIR])


@pytest.fixture(scope="session")
def engine():
    # return create_engine(f"sqlite:///{BASE_DIR}/transcriptor_test.db")
    return Database(f"{BASE_DIR}/transcriptor.db").engine


@pytest.fixture(scope="session")
def tables(engine):
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def dbsession(engine, tables):
    connection = engine.connect()
    transaction = connection.begin()

    session = Session(bind=connection)
    yield session

    session.close()
    transaction.rollback()
    connection.close()
