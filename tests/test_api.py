import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from transcriptor.api import API, Client


@pytest.fixture
def api_instance():
    base_dir = Path(__file__).parent
    return API(base_dir)


@pytest.fixture
def mock_session():
    with patch("transcriptor.database.Database"):
        mock_session = MagicMock()
        yield mock_session


def test_add_client(api_instance, mock_session):
    api_instance.session = mock_session

    client = {"name": "Client1"}
    api_instance.add_client(client)

    assert len(mock_session.add.call_args[0]) == 1
    mock_session.commit.assert_called_once()


def test_add_rates(api_instance, mock_session):
    api_instance.session = mock_session

    rates = {"normal": 0.4, "expedite": 0.6, "interpreted": 0.3}
    api_instance.add_rates(rates)

    assert len(mock_session.add.call_args[0]) == 1
    mock_session.commit.assert_called_once()


def test_add_job(api_instance, mock_session):
    api_instance.session = mock_session

    jobs = {"id": 1}
    api_instance.add_job(jobs)

    assert len(mock_session.add.call_args[0]) == 1
    mock_session.commit.assert_called_once()


def test_get_clients(api_instance, mock_session):
    api_instance.session = mock_session
    mock_session.scalars.return_value.all.return_value = ["client1", "client2"]

    clients = api_instance.get_clients()

    mock_session.scalars.assert_called_once()
    assert clients == ["client1", "client2"]


def test_update(api_instance, mock_session):
    api_instance.session = mock_session

    result = api_instance.update(Client, {"name": "old_name"}, {"name": "new_name"})

    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()
    assert result


def test_delete(api_instance, mock_session):
    api_instance.session = mock_session
    mock_session.execute.return_value.rowcount = 1

    result = api_instance.delete(Client, {"name": "client1"})

    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()
    assert result


def test_delete_no_match(api_instance, mock_session):
    api_instance.session = mock_session
    mock_session.execute.return_value.rowcount = 0

    result = api_instance.delete(Client, {"name": "non_existing_client"})

    mock_session.execute.assert_called_once()
    mock_session.commit.assert_not_called()
    assert not result
