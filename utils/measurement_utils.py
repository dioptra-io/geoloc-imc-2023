import ujson as json

from random import randint
from ipaddress import IPv4Network


def load_json(file):
    with open(file) as f:
        return json.load(f)


def dump_json(o, file):
    with open(file, "w") as f:
        json.dump(o, f, indent=4)


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
