import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from transcriptor.database import Base, Database

os.environ["TRANS_ENV"] = "DEV"

# BASE_DIR = Path(__file__).parent.joinpath("data")
# mkdirp([BASE_DIR])
# # print(os.environ)

# @pytest.fixture
@pytest.fixture(scope="session")
def base_dir():
    temp_dir = tempfile.mkdtemp()
    return temp_dir


@pytest.fixture(scope="session")
def engine(base_dir):
    # return create_engine(f"sqlite:///{BASE_DIR}/transcriptor_test.db")
    # temp_dir = tempfile.mkdtemp()
    db_path = Path(base_dir).joinpath("transcriptor.db")
    return Database(f"{db_path}").engine


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
