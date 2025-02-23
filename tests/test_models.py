import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from transcriptor.models import Base, Client, Rate, Job, Profile, Config

engine = create_engine("sqlite:///:memory:", echo=True)
SessionLocal = sessionmaker(bind=engine)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def session():
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="module")
def seed_clients(session):
    """Seed the database with initial clients."""
    client = Client(name="Test Client", email="test@example.com")
    session.add(client)
    session.commit()
    return client


@pytest.mark.parametrize(
    "client_data, expected_result",
    [
        ({"name": "Client A", "email": "clienta@example.com"}, True),
        ({"name": "Client B", "email": "clientb@example.com"}, True),
        ({"name": "Client A", "email": "clientc@example.com"}, False),  # Duplicate name
        (
            {"name": "Client C", "email": "clienta@example.com"},
            True,
        ),  # Duplicate email is allowed
        ({"name": None, "email": "clientd@example.com"}, False),  # Null name
        ({"name": "Client E", "email": None}, False),  # Null email
    ],
)
def test_client_insertion(session: Session, client_data, expected_result):
    client = Client(**client_data)
    try:
        session.add(client)
        session.commit()
        assert expected_result is True
    except (IntegrityError, AssertionError):
        session.rollback()
        assert expected_result is False


@pytest.mark.parametrize(
    "rate_data, expected_result",
    [
        (
            {"normal": 100.0, "expedite": 150.0, "interpreted": 200.0, "client_id": 1},
            True,
        ),
        (
            {"normal": None, "expedite": 150.0, "interpreted": 200.0, "client_id": 1},
            False,
        ),  # Null normal
        (
            {"normal": 100.0, "expedite": None, "interpreted": 200.0, "client_id": 1},
            False,
        ),  # Null expedite
        (
            {"normal": 100.0, "expedite": 150.0, "interpreted": None, "client_id": 1},
            False,
        ),  # Null interpreted
        (
            {"normal": 100.0, "expedite": 150.0, "interpreted": 200.0, "client_id": 99},
            False,
        ),  # Invalid client_id
        (
            {
                "normal": 100.0,
                "expedite": 150.0,
                "interpreted": 200.0,
                "client_id": None,
            },
            False,
        ),  # No client_id
    ],
)
def test_rate_insertion(session: Session, seed_clients, rate_data, expected_result):
    rate = Rate(**rate_data)
    try:
        session.add(rate)
        session.commit()
        assert expected_result is True
    except (IntegrityError, AssertionError):
        session.rollback()
        assert expected_result is False


@pytest.mark.parametrize(
    "job_data, expected_result",
    [
        # Valid job insertion
        (
            {
                "client_id": 1,
                "date_received": "2023-10-10",
                "job_number": "JOB123",
                "job_type": "Translation",
                "date_due": "2023-11-10",
                "total_quantity": 100.0,
                "quantity": 10.0,
                "job_rate": 20.0,
                "amount": 200.0,
                "job_path": "/jobs/JOB123",
            },
            True,
        ),
        # Null constraints testing
        (
            {
                **{
                    k: v
                    for k, v in {
                        "client_id": 1,
                        "date_received": "2023-10-10",
                        "job_number": "JOB123",
                        "job_type": "Translation",
                        "date_due": "2023-11-10",
                        "total_quantity": 100.0,
                        "quantity": 10.0,
                        "job_rate": 20.0,
                        "amount": 200.0,
                        "job_path": "/jobs/JOB123",
                    }.items()
                    if k != "date_received"
                },
                "date_received": None,
            },
            False,
        ),  # Null date_received
        # ...repeat for each non-nullable field
        (
            {
                **{
                    k: v
                    for k, v in {
                        "client_id": 1,
                        "date_received": "2023-10-10",
                        "job_number": "JOB123",
                        "job_type": "Translation",
                        "date_due": "2023-11-10",
                        "total_quantity": 100.0,
                        "quantity": 10.0,
                        "job_rate": 20.0,
                        "amount": 200.0,
                        "job_path": "/jobs/JOB123",
                    }.items()
                    if k != "job_number"
                },
                "job_number": None,
            },
            False,
        ),
        # Invalid client id
        (
            {
                "client_id": 999,
                "date_received": "2023-10-10",
                "job_number": "JOB124",
                "job_type": "Editing",
                "date_due": "2023-11-15",
                "total_quantity": 50.0,
                "quantity": 5.0,
                "job_rate": 15.0,
                "amount": 75.0,
                "job_path": "/jobs/JOB124",
            },
            False,
        ),
    ],
)
def test_job_insertion(session: Session, seed_clients, job_data, expected_result):
    job = Job(**job_data)
    try:
        session.add(job)
        session.commit()
        assert expected_result is True
    except (IntegrityError, AssertionError):
        session.rollback()
        assert expected_result is False


@pytest.mark.parametrize(
    "profile_data, expected_result",
    [
        # Valid profile insertion
        (
            {
                "first_name": "John",
                "last_name": "Doe",
                "area": "Nairobi",
                "country": "Kenya",
            },
            True,
        ),
        # Null checks for each field
        (
            {
                "first_name": None,
                "last_name": "Doe",
                "area": "Nairobi",
                "country": "Kenya",
            },
            False,
        ),
        (
            {
                "first_name": "John",
                "last_name": None,
                "area": "Nairobi",
                "country": "Kenya",
            },
            False,
        ),
        (
            {
                "first_name": "John",
                "last_name": "Doe",
                "area": None,
                "country": "Kenya",
            },
            False,
        ),
        (
            {
                "first_name": "John",
                "last_name": "Doe",
                "area": "Nairobi",
                "country": None,
            },
            False,
        ),
    ],
)
def test_profile_insertion(session: Session, profile_data, expected_result):
    profile = Profile(**profile_data)
    try:
        session.add(profile)
        session.commit()
        assert expected_result is True
    except (IntegrityError, AssertionError):
        session.rollback()
        assert expected_result is False


@pytest.mark.parametrize(
    "config_data, expected_result",
    [
        # Valid config insertion
        (
            {
                "key": "theme",
                "value": "dark",
            },
            True,
        ),
        # Null checks for each field
        (
            {"key": None, "value": "dark"},
            False,
        ),
        (
            {"key": "theme", "value": None},
            False,
        ),
    ],
)
def test_config_insertion(session: Session, config_data, expected_result):
    config = Config(**config_data)
    try:
        session.add(config)
        session.commit()
        assert expected_result is True
    except (IntegrityError, AssertionError):
        session.rollback()
        assert expected_result is False
