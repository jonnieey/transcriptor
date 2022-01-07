import inquirer
from inquirer import Text

def input_menu(name, msg, default=None):
    question = [ Text(name=name, message=msg)]
    answer = inquirer.prompt(question)
    return answer
