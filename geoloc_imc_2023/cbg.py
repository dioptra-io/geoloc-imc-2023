import logging
import time

from random import randint
from collections import OrderedDict
from copy import deepcopy
from ipaddress import IPv4Network

from geoloc_imc_2023.atlas_probing import RIPEAtlas
from geoloc_imc_2023.default import (
    NB_PACKETS,
    NB_TARGETS_PER_PREFIX,
    MAX_NUMBER_OF_VPS,
    NB_MAX_CONCURRENT_MEASUREMENTS,
)

logger = logging.getLogger()


def get_prefix_from_ip(addr: str):
    """from an ip addr return /24 prefix"""
    prefix = addr.split(".")[:-1]
    prefix.append("0")
    prefix = ".".join(prefix)

    return prefix


class CBG:
    def __init__(
        self,
        ripe_credentials: dict[str, str],
    ) -> None:
        self.account = ripe_credentials["username"]
        self.key = ripe_credentials["key"]

        self.driver = RIPEAtlas(self.account, self.key)

    def get_target_hitlist(
        self, target_prefix: str, nb_targets: int, targets_per_prefix: dict
    ) -> list[str]:
        """from ip, return a list of target ips"""
        target_addr_list = []
        try:
            target_addr_list = targets_per_prefix[target_prefix]
        except KeyError:
            pass
        if len(target_addr_list) < nb_targets:
            prefix = IPv4Network(target_prefix + "/24")
            target_addr_list.extend(
                [
                    str(prefix[randint(1, 254)])
                    for _ in range(0, nb_targets - len(target_addr_list))
                ]
            )
            print(target_addr_list)

        if len(target_addr_list) > nb_targets:
            target_addr_list = target_addr_list[:nb_targets]

        return target_addr_list

    def prefix_probing(
        self,
        target_prefixes: list,
        vps: dict,
        targets_per_prefix: dict,
        tag: str,
        nb_packets: int = NB_PACKETS,
        nb_targets: int = NB_TARGETS_PER_PREFIX,
        dry_run: bool = False,
    ) -> dict:
        """from a list of prefixes, start measurements for n target addrs in prefix"""

        measurement_ids = OrderedDict()
        for _, target_prefix in enumerate(target_prefixes):
            # get target_addr_list
            target_addr_list = self.get_target_hitlist(
                target_prefix, nb_targets, targets_per_prefix
            )

            vp_ids = [
                vps[vp_addr]["id"] for vp_addr in vps if vp_addr not in target_addr_list
            ]

            logger.info(
                f"starting measurement for {target_prefix=} with {[addr for addr in target_addr_list]} with {len(ids)} vps"
            )

            for i in range(0, len(vp_ids), MAX_NUMBER_OF_VPS):
                ids = vp_ids[i : i + MAX_NUMBER_OF_VPS]

                for target_addr in target_addr_list:
                    if not dry_run:
                        measurement_id = self.driver.probe(
                            str(target_addr), ids, tag, nb_packets
                        )
                        try:
                            measurement_ids[target_prefix].append(measurement_id)
                        except KeyError:
                            measurement_ids[target_prefix] = [measurement_id]

                    else:
                        logger.debug(f"measurement for {target_addr}")
                        measurement_id = 404
                        try:
                            measurement_ids[target_addr].append(measurement_id)
                        except KeyError:
                            measurement_ids[target_addr] = [measurement_id]

                    # check the numner of running measurements
                    active_measurements = sum(
                        [len(target_ids) for target_ids in measurement_ids.values()]
                    )

                    # check number of parrallele measurements in not too high
                    if active_measurements > NB_MAX_CONCURRENT_MEASUREMENTS:
                        logger.info(
                            f"Reached limit for number of conccurent measurements: {active_measurements} (limit is {NB_MAX_CONCURRENT_MEASUREMENTS})"
                        )
                        temp_ids = deepcopy(measurement_ids)
                        for prefix, ids in temp_ids.items():
                            # wait for the last measurement of the batch to end before starting a new one
                            for id in ids:
                                if not dry_run:
                                    resp = self.driver._wait_for(id)
                                # else: time.sleep(1)

                            measurement_ids.pop(prefix)

        return measurement_ids

    def target_probing(
        self,
        targets: list,
        vps: dict,
        tag: str,
        nb_packets: int = NB_PACKETS,
        dry_run: bool = False,
    ) -> dict:
        """from a list of prefixes, start measurements for n target addrs in prefix"""

        measurement_ids = OrderedDict()
        for _, target_addr in enumerate(targets):
            # get target_addr_list
            vp_ids = [vps[vp_addr]["id"] for vp_addr in vps if vp_addr != target_addr]

            for i in range(0, len(vp_ids), MAX_NUMBER_OF_VPS):
                ids = vp_ids[i : i + MAX_NUMBER_OF_VPS]

                logger.info(
                    f"starting measurement for {target_addr=} with {len(ids)} vps"
                )

                if dry_run:
                    measurement_id = self.driver.probe(
                        str(target_addr), ids, tag, nb_packets
                    )

                    try:
                        measurement_ids[target_addr].append(measurement_id)
                    except KeyError:
                        measurement_ids[target_addr] = [measurement_id]
                else:
                    measurement_id = 404
                    try:
                        measurement_ids[target_addr].append(measurement_id)
                    except KeyError:
                        measurement_ids[target_addr] = [measurement_id]

                # check the numner of running measurements
                active_measurements = sum(
                    [len(target_ids) for target_ids in measurement_ids.values()]
                )

                # check number of parrallele measurements in not too high
                if active_measurements > NB_MAX_CONCURRENT_MEASUREMENTS:
                    temp_ids = deepcopy(measurement_ids)
                    for addr, ids in temp_ids.items():
                        # wait for the last measurement of the batch to end before starting a new one
                        for id in ids:
                            if not dry_run:
                                resp = self.driver._wait_for(id)
                            else:
                                time.sleep(1)

                        measurement_ids.pop(addr)

        return measurement_ids
