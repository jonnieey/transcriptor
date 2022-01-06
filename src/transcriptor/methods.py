from transcriptor.client import Client

def create_client(name, email) -> Client:
    client = Client(name, email)
    return client

def save_client_to_file(client):
    client_json = client.to_json()
    try:
        with open('clients.txt', 'w') as fp:
            fp.write(client_json)
        return True
    except Exception as error:
        print(error)
        return False
