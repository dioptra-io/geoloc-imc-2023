import pickle
import logging
import requests
import time

from pathlib import Path
from random import randint, choice
from ipaddress import IPv4Network
from collections import defaultdict

from geoloc_imc_2023.atlas_probing import RIPEAtlas
from geoloc_imc_2023.default import (
    NB_PACKETS,
    HITLIST_ADDR_PATH,
    ANCHOR_PATH,
)

logger = logging.getLogger()

def get_prefix_from_ip(addr: str):
    """from an ip addr return /24 prefix"""
    prefix = addr.split(".")[:-1]
    prefix.append("0")
    prefix = ".".join(prefix)

    return prefix

class CBG():
    def __init__(
            self,
            targets: list,
            vps: list,
            ripe_credentials: dict[str, str],
            hitlist_addr: dict,
            anchors: dict,
        ) -> None:

        self.targets = targets
        self.vps = vps
        self.anchors = anchors
        self.hitlist_addr = hitlist_addr
        self.account = ripe_credentials["username"]
        self.key = ripe_credentials["key"]

        self.driver = RIPEAtlas(self.account, self.key)

    def get_target_hitlist(self, target_prefix: str, hitlist_size: int = 3) -> list[str]:
        """from ip, return a list of target ips"""
        target_addr_list = []
        try:
            target_addr_list = self.hitlist_addr[target_prefix]
        except KeyError:
            pass

        if len(target_addr_list) < hitlist_size:
            target_addr_list.extend([str(target_prefix[randint(1,254)]) for _ in range(0,hitlist_size - len(target_addr_list))])
        if len(target_addr_list) > hitlist_size:
            target_addr_list = target_addr_list[:hitlist_size]

        return target_addr_list

    def start_init_measurements(self, target_prefixes: list, nb_target_addr: int = 3, nb_packets: int = NB_PACKETS) -> dict:
        """from a list of prefixes, start measurements for n target addrs in prefix"""
        measurement_ids = defaultdict(list)
        dry_run = False
        for _, target_prefix in enumerate(target_prefixes):

            # get target_addr_list
            target_addr_list = self.get_target_hitlist(target_prefix, nb_target_addr)

            vp_ids = [self.anchors[vp_addr]['id'] for vp_addr in self.vps if vp_addr not in target_addr_list]

            logger.info(f"starting measurement for {target_prefix=} with {[addr for addr in target_addr_list]} with {len(self.vps)} self.anchors")    

            for target_addr in target_addr_list:
                if dry_run:
                    logger.debug(f"measurement for {target_addr}")
                    continue
                else:
                    # TODO: parralelize post requests otherwise it takes too much time
                    measurement_id = self.driver.probe(str(target_addr), vp_ids, nb_packets)
                    measurement_ids[target_prefix].append(measurement_id)
        
        return measurement_ids

    def start_target_measurements(self, target_list: list, vp_list: list, nb_packets: int = NB_PACKETS) -> dict:
        measurement_ids = {}
        for _, target_addr in enumerate(target_list):
            measurement_id = self.start_single_measurement(target_addr, vp_list, nb_packets)
            measurement_ids[target_addr] = measurement_id
        return measurement_ids

    def start_single_measurement(self, target_addr: str, vps: list, nb_packets: int = NB_PACKETS):
        """probe a single target addr with a list of vp"""
        vp_ids = [self.anchors[vp_addr]['id'] for vp_addr in vps if vp_addr != target_addr]
        measurement_id = self.driver.probe(str(target_addr), vp_ids, nb_packets)

        return measurement_id


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    NB_TARGET = 10
    NB_VP = 10
    ripe_credentials = {
        "username": "timur.friedman@sorbonne-universite.fr",
        "key": "b3d3d4fc-724e-4505-befe-1ad16a70dc87",
    }

    # load anchors
    with open(ANCHOR_PATH, "rb") as f:
        anchors = pickle.load(f)
    
    with open(HITLIST_ADDR_PATH, "rb") as f:
        hitlist_addr = pickle.load(f)

    targets= [choice(list(anchors)) for _ in range(0, NB_TARGET)]
    vps = list(set(anchors).difference(set(targets)))[:NB_VP]

    logging.info(f"nb targets: {len(targets)} : {[target for target in targets]}")
    logging.info(f"nb_vps : {len(vps)} {[vp for vp in vps]} ")

    cbg = CBG(targets, vps, ripe_credentials, hitlist_addr, anchors)

    # get target prefixes
    target_prefixes = []
    for target_addr in targets:
        target_prefix = get_prefix_from_ip(target_addr)
        target_prefixes.append(target_prefix)
    
    # initialization: start measurements from all vps to targets
    init_measurement_ids = cbg.start_init_measurements(target_prefixes)

    # retreive measurement results from RIPE Atlas
    logging.info(init_measurement_ids)

    

    
    

    
  

            