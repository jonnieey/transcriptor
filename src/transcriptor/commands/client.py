import click
from transcriptor.api import add_client

@click.group()
def cli(**kwargs):
    "Clients actions"
    pass

@cli.command()
@click.option('-n', '--name', required=True, help="Specify new client's name")
@click.option('-e', '--email', required=True, help="Specify new client's email")
def add(name, email):
    """Add client"""
    add_client(name, email)

# import click
#
#
# @click.group()
# def cli(**kwargs):
#     print(1)
#
#
# @cli.group()
# @click.option("--something")
# @click.option("--else")
# def what(**kwargs):
#     print(2)
#
#
# @what.command()
# @click.option("--chaa")
# def ever(**kwargs):
#     print(3)
#
#
# if __name__ == '__main__':
#     cli()
#
