import pytest
import io
import json

from transcriptor.client import Client
from transcriptor.methods import create_client

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

def test_create_client():
    client = create_client(name=CLIENT_NAME, email=CLIENT_EMAIL)
    assert isinstance(client, Client) is True
    assert client.name == CLIENT_NAME

def test_save_client_to_file(test_client):
    pass

