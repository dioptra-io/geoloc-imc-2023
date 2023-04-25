import pickle
import logging

from pathlib import Path
from random import randint, choice
from collections import defaultdict

from geoloc_imc_2023.atlas_probing import RIPEAtlas
from geoloc_imc_2023.default import (
    NB_PACKETS,
    NB_TARGETS_PER_PREFIX,
    HITLIST_PATH,
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
        ) -> None:

        self.account = ripe_credentials["username"]
        self.key = ripe_credentials["key"]

        self.driver = RIPEAtlas(self.account, self.key)


    def get_target_hitlist(self, target_prefix: str, nb_targets: int, targets_per_prefix: dict) -> list[str]:
        """from ip, return a list of target ips"""
        target_addr_list = []
        try:
            target_addr_list = targets_per_prefix[target_prefix]
        except KeyError:
            pass

        if len(target_addr_list) < nb_targets:
            target_addr_list.extend([str(target_prefix[randint(1,254)]) for _ in range(0,nb_targets - len(target_addr_list))])
        if len(target_addr_list) > nb_targets:
            target_addr_list = target_addr_list[:nb_targets]

        return target_addr_list

    def prefix_probing(
            self, 
            target_prefixes: list,
            vps: dict,
            targets_per_prefix: dict,
            nb_packets: int = NB_PACKETS, 
            nb_targets: int = NB_TARGETS_PER_PREFIX,
            dry_run: bool = False,
        ) -> dict:
        """from a list of prefixes, start measurements for n target addrs in prefix"""
        measurement_ids = defaultdict(list)
        for _, target_prefix in enumerate(target_prefixes):

            # get target_addr_list
            target_addr_list = self.get_target_hitlist(target_prefix, nb_targets, targets_per_prefix)

            vp_ids = [vps[vp_addr]['id'] for vp_addr in vps if vp_addr not in target_addr_list]

            logger.info(f"starting measurement for {target_prefix=} with {[addr for addr in target_addr_list]} with {len(vps)}")    

            for target_addr in target_addr_list:
                if dry_run:
                    logger.debug(f"measurement for {target_addr}")
                    measurement_id = 404
                    measurement_ids[target_prefix].append(measurement_id)
                    continue
                else:
                    measurement_id = self.driver.probe(str(target_addr), vp_ids, nb_packets)
                    measurement_ids[target_prefix].append(measurement_id)
        
        return measurement_ids

    def target_probing(
            self,
            targets: list,
            vps: dict,
            nb_packets: int = NB_PACKETS,
            dry_run: bool = False
        ) -> dict:
        """from a list of prefixes, start measurements for n target addrs in prefix"""
        measurement_ids = defaultdict(list)
        for _, target_addr in enumerate(targets):

            # get target_addr_list
            vp_ids = [vps[vp_addr]['id'] for vp_addr in vps if vp_addr != target_addr]

            logger.info(f"starting measurement for {target_addr=} with {len(vps)} self.anchors")    

            if dry_run:
                measurement_id = 404
                measurement_ids[target_addr].append(measurement_id)
                continue
            else:
                measurement_id = self.driver.probe(str(target_addr), vp_ids, nb_packets)
                measurement_ids[target_addr].append(measurement_id)
        
        return measurement_ids    

    
    

    
  

            