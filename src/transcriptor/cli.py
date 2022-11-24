from pathlib import Path

import click

plugin_folder = Path(__file__).parent.joinpath("commands")


class MyCLI(click.MultiCommand):
    def list_commands(self, ctx):
        rv = []
        for filename in plugin_folder.iterdir():
            if filename.suffix.endswith(".py") and filename.name != "__init__.py":
                rv.append(filename.stem)
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        ns = {}
        fn = Path(plugin_folder).joinpath(name + ".py")
        with open(fn) as f:
            code = compile(f.read(), fn, "exec")
            eval(code, ns, ns)
        return ns["cli"]


cli = MyCLI(help="Subcommands are loaded from a " "plugin folder dynamically.")
if __name__ == "__main__":
    cli()
