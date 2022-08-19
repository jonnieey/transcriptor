import os
from pathlib import Path


def get_config_path(app_name):
    config_path = Path().joinpath(
        os.environ.get("APPDATA")
        or os.environ.get("XDG_CONFIG_HOME")
        or Path().joinpath(os.environ["HOME"], ".config"),
        app_name,
    )
    return config_path


def touch(file_path: Path):
    if not file_path.exists():
        file_path.parent.mkdir(exist_ok=True, parents=True)
        file_path.touch(exist_ok=True)


def snake_case(string: str):
    return string.replace(" ", "_")


def kebab_case(string: str):
    return string.replace(" ", "-")
