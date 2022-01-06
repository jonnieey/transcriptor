import pytest

from transcriptor.client import Client

CLIENT_NAME = 'TestClient'
CLIENT_EMAIL = 'TestEmail'

@pytest.fixture()
def test_client():
    return Client(name=CLIENT_NAME, email=CLIENT_EMAIL)

def test_client_to_dict(test_client):

    client_json = {
        "name": "TestClient",
        "email": "TestEmail",
    }

    assert test_client.to_dict() == client_json


