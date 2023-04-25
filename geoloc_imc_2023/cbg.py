import pickle
import logging

from random import randint, choice
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
            ripe_credentials: dict[str, str],
            hitlist_addr: dict,
            anchors: dict,
            nb_target_addr: int = 3,
            nb_packets: int = 3,
        ) -> None:

        self.anchors = anchors
        self.hitlist_addr = hitlist_addr
        self.account = ripe_credentials["username"]
        self.key = ripe_credentials["key"]
        self.nb_target_addr = nb_target_addr
        self.nb_packets = nb_packets

        self.driver = RIPEAtlas(self.account, self.key, self.anchors)

    def get_target_hitlist(self, target_prefix: str) -> list[str]:
        """from ip, return a list of target ips"""
        target_addr_list = []
        try:
            target_addr_list = self.hitlist_addr[target_prefix]
        except KeyError:
            pass

        if len(target_addr_list) < self.nb_target_addr:
            target_addr_list.extend([str(target_prefix[randint(1,254)]) for _ in range(0,self.nb_target_addr - len(target_addr_list))])
        if len(target_addr_list) > self.nb_target_addr:
            target_addr_list = target_addr_list[:self.nb_target_addr]

        return target_addr_list

    def prefix_probing(self, target_prefixes: list, vps: list, nb_packets: int = NB_PACKETS) -> dict:
        """from a list of prefixes, start measurements for n target addrs in prefix"""
        measurement_ids = defaultdict(list)
        dry_run = False
        for _, target_prefix in enumerate(target_prefixes):

            # get target_addr_list
            target_addr_list = self.get_target_hitlist(target_prefix, self.nb_target_addr)

            vp_ids = [self.anchors[vp_addr]['id'] for vp_addr in vps if vp_addr not in target_addr_list]

            logger.info(f"starting measurement for {target_prefix=} with {[addr for addr in target_addr_list]} with {len(vps)} self.anchors")    

            for target_addr in target_addr_list:
                if dry_run:
                    logger.debug(f"measurement for {target_addr}")
                    continue
                else:
                    measurement_id = self.driver.probe(str(target_addr), vp_ids, nb_packets)
                    measurement_ids[target_prefix].append(measurement_id)
        
        return measurement_ids

    def target_probing(self, targets: list, vps: list, nb_packets: int = NB_PACKETS) -> dict:
        """from a list of prefixes, start measurements for n target addrs in prefix"""
        measurement_ids = defaultdict(list)
        dry_run = False
        for _, target_addr in enumerate(targets):

            # get target_addr_list
            vp_ids = [self.anchors[vp_addr]['id'] for vp_addr in vps if vp_addr != target_addr]

            logger.info(f"starting measurement for {target_addr=} with {len(vps)} self.anchors")    

            for target_addr in target_addr:
                if dry_run:
                    logger.debug(f"measurement for {target_addr}")
                    continue
                else:
                    measurement_id = self.driver.probe(str(target_addr), vp_ids, nb_packets)
                    measurement_ids[target_prefix].append(measurement_id)
        
        return measurement_ids


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

    

    
    

    
  

            