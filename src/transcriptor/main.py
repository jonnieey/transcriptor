from pathlib import Path
import shutil

from transcriptor.client import Client

from transcriptor.methods import (
    check_settings,
    create_task,
    save_client_to_file,
    get_date_received,
    get_all_clients,
    get_job_details_from_zip,
    save_client_job_to_file
)

from transcriptor.ui import (
    text_add_client,
    raw_menu_client_list,
    text_job_quantity,
    raw_menu_job_type,
    text_get_date,
    text_input_generic,
    text_get_date_received,
)
from transcriptor.utils import get_media_files, extract_zip_to, get_media_duration

settings = check_settings()

def add_client():
    clients_folder = Path(settings.clients_folder)
    client_dict = text_add_client()
    client = Client.from_json(client_dict)
    save_client_to_file(client=client, clients_folder=clients_folder)
    return client

def select_client():
    clients_folder = Path(settings.clients_folder)
    all_clients = get_all_clients(clients_folder)
    if all_clients == []:
        return add_client()
    else:
        client_name = raw_menu_client_list([c.name for c in all_clients])
        for client_obj in all_clients:
            if client_obj.name == client_name['client']:
                client =  client_obj
                return client
            else:
                continue

def create_job(zip_file, work_folder, client, date_received, job_number, date_due, job_folder):
    tasks = []
    task_folder_name = "%s-%s_DUE_%s" % (date_received, job_number, date_due)
    print(task_folder_name)
    task_path = work_folder / client.name / task_folder_name

    if not task_path.exists():
        task_path.mkdir(parents=True, exist_ok=True)

    new_zip_file = shutil.copy2(zip_file, task_path) # should move
    extract_zip_to(new_zip_file, task_path)

    task_media_files = get_media_files(task_path)
    for media_file in task_media_files:
        job_type = raw_menu_job_type(media_file)
        total_quantity = get_media_duration(media_file)
        quantity = text_job_quantity(media_file)

        task = create_task(
            date_received=date_received,
            job_number=job_number,
            job_type=job_type,
            total_quantity=total_quantity,
            quantity=quantity,
            date_due=date_due,
        )
        tasks.append(task)
        # get quantity, total_quantity

    save_client_job_to_file(client, tasks, job_folder)

if __name__ == "__main__":
    client = select_client()
    work_folder = Path(settings.work_folder)
    job_folder = Path(settings.job_folder)

    zip_file = Path("/home/kamikaze/Documents/Wera/Transcription/Jonnieey/Natalie Puelles/2021-11-04-513072/513072.zip")

    date_received = get_date_received()
    if date_received is None:
        d = text_get_date_received(zip_file)
        date_received = get_date_received(d)

    job_number, date_due = get_job_details_from_zip(zip_file)
    if job_number is None:
        job_number = text_input_generic(name='job_number')

    if date_due is None:
        d = text_get_date('due')
        date_due = get_date_received(d)
    # if date_due == '':
    #     date_due = None
    j = create_job(
        zip_file=zip_file,
        work_folder=work_folder,
        client=client,
        date_received=date_received,
        job_number=job_number,
        date_due=date_due,
        job_folder=job_folder,
    )
