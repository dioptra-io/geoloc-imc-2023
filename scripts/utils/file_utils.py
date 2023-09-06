"""Functions to load and save data into a json format.
All the paths are given in default.py file.
"""

import ujson as json

from pathlib import Path

def load_json(file_path: Path):
    # check that dirs exits
    if not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path) as f:
        return json.load(f)


def dump_json(data, file_path: Path):
    """dump data to output file"""
    # check that dirs exits
    if not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)
