import pytest

from transcriptor.client import Client
from transcriptor.main import create_client

def test_client_to_dict():
    client = Client()
    client.name = "TestClient"
    client.email = "TestEmail"

    client_json = {
        "name": "TestClient",
        "email": "TestEmail",
    }

    assert client.to_dict() == client_json

def test_create_new_client():
    client = create_client(name='TestClient', email='TestEmail')
    assert isinstance(client, Client)

