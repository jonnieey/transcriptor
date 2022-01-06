import pytest

from transcriptor.client import Client

def test_client_to_dict():
    client = Client()
    client.name = "TestClient"
    client.email = "TestEmail"

    client_json = {
        "name": "TestClient",
        "email": "TestEmail",
    }

    assert client.to_dict() == client_json


