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

