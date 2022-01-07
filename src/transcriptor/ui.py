import inquirer
from inquirer import Text
from inquirer.themes import GreenPassion

def input_menu(name, msg, default=None):
    question = [ Text(name=name, message=msg)]
    answer = inquirer.prompt(question, theme=GreenPassion())
    return answer


