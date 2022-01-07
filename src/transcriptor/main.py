from transcriptor.ui import text_add_client, raw_menu_client_list
from transcriptor.client import Client
from transcriptor.methods import save_client_to_file, check_settings, get_all_clients
from pathlib import Path

settings = check_settings()

def add_client():
    clients_folder = Path(settings.clients_folder)
    client_dict = text_add_client()
    client = Client.from_json(client_dict)
    save_client_to_file(client=client, clients_folder=clients_folder)

def select_client():
    clients_folder = Path(settings.clients_folder)
    all_clients = get_all_clients(clients_folder)
    client_name = raw_menu_client_list([c.name for c in all_clients])
    for client_obj in all_clients:
        if client_obj.name == client_name['client']:
            client =  client_obj
            break
        else:
            continue
    return client

if __name__ == "__main__":
    print(select_client().email)
