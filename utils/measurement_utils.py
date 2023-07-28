import pickle
import ujson as json

from pathlib import Path
from random import randint
from ipaddress import IPv4Network


def load_json(file):
    with open(file) as f:
        return json.load(f)


def dump_json(o, file):
    with open(file, "w") as f:
        json.dump(o, f)


def load_pickle(file):
    with open(file, "rb") as f:
        return pickle.load(f)


def dump_pickle(o, file):
    with open(file, "wb") as f:
        pickle.dump(o, f)


def update_pickle(subset_results: dict, file: Path) -> None:
    try:
        cached_results = load_pickle(file)
        cached_results.update(subset_results)
    except FileNotFoundError:
        cached_results = subset_results
    dump_json(cached_results, file)


def save_config_file(measurement_config: dict, file: Path) -> None:
    """save measurement config file"""
    with open(file, "w") as f:
        json.dump(measurement_config, f, indent=4)


def get_prefix_from_ip(addr: str) -> str:
    """from an ip addr return /24 prefix"""
    prefix = addr.split(".")[:-1]
    prefix.append("0")
    prefix = ".".join(prefix)

    return prefix


def get_target_hitlist(
        target_prefix: str, nb_targets: int, targets_per_prefix: dict
) -> list:
    """from ip, return a list of target ips"""
    target_addr_list = []
    try:
        target_addr_list = targets_per_prefix[target_prefix]
    except KeyError:
        pass

    target_addr_list = list(set(target_addr_list))

    if len(target_addr_list) < nb_targets:
        prefix = IPv4Network(target_prefix + "/24")
        target_addr_list.extend(
            [
                str(prefix[randint(1, 254)])
                for _ in range(0, nb_targets - len(target_addr_list))
            ]
        )

    if len(target_addr_list) > nb_targets:
        target_addr_list = target_addr_list[:nb_targets]

    return target_addr_list
