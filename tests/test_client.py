import pytest

from transcriptor.client import Client

CLIENT_NAME = "TestClient"
CLIENT_EMAIL = "TestEmail"


@pytest.fixture()
def test_client():
    return Client(name=CLIENT_NAME, email=CLIENT_EMAIL)


def test_client_to_dict(test_client):
    client_dict = {"name": "TestClient", "email": "TestEmail"}

    assert test_client.to_dict() == client_dict


def test_client_to_json(test_client):
    client_json = '{\n  "email": "TestEmail",\n  "name": "TestClient"\n}'

    assert test_client.to_json() == client_json


def test_client_from_json(test_client):
    client_json = test_client.to_json()
    client_obj = Client().from_json(client_json)

    assert isinstance(client_obj, Client)
    assert client_obj.name == CLIENT_NAME
