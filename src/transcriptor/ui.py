import questionary
from questionary import prompt

def input_menu(name, msg, default=None):
    answer  = questionary.text(msg).ask()
    return answer

def raw_menu_client_list(clients_list):
    questions = [
        {
            "type": "rawselect",
            "name": "client",
            "message": "Select item",
            "choices": clients_list,
        },
    ]
    return prompt(questions)

def text_add_client():
    questions = [
        {
            "type": "text",
            "name": "name",
            "message": "Enter client's name",
        },
        {
            "type": "text",
            "name": "email",
            "message": "Enter client's email",
        },
    ]

    return prompt(questions)

def raw_menu_job_type(file_path):
    job_types = ['Normal', 'Interpreted', 'Expedite']
    questions = [
        {
            "type": "rawselect",
            "name": "job_type",
            "message": f"Select job type: {file_path}",
            "choices": job_types,
        },
    ]
    return prompt(questions)['job_type']

def text_job_quantity(file_path):
    questions = [
        {
            "type": "text",
            "name": "job_quantity",
            "message": f"Enter Duration: {file_path.name}",
        },
    ]

    return prompt(questions)['job_quantity']

def text_get_date(date_msg):
    questions = [
        {
            "type": "text",
            "name": "date",
            "message": f"Enter date: {date_msg}",
        },
    ]

    return prompt(questions)['date']

def text_input_generic(name):
    msg_str = name.replace("_", " ")

    questions = [
        {
            "type": "text",
            "name": name,
            "message": f"Enter {msg_str}",
        },
    ]

    return prompt(questions)['name']
