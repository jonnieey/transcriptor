import os
from pathlib import Path


def touch(file_path: Path):
    if not file_path.exists():
        file_path.parent.mkdir(exist_ok=True, parents=True)
        file_path.touch(exist_ok=True)


def sc(string: str):
    return string.replace(" ", "_")


def nc(string: str):
    return string.replace("_", " ")


def kebab_case(string: str):
    return string.replace(" ", "-")
