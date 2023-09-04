# Functions to load and save data into a json format.

# All the paths are given in default.py file.

import ujson as json


def load_json(file):
    with open(file) as f:
        return json.load(f)


def dump_json(data, file):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)
