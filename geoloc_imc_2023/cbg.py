import logging
import time

from copy import copy
from random import randint
from ipaddress import IPv4Network

from geoloc_imc_2023.atlas_probing import RIPEAtlas
from geoloc_imc_2023.default import (
    NB_PACKETS,
    NB_TARGETS_PER_PREFIX,
    MAX_NUMBER_OF_VPS,
    NB_MAX_CONCURRENT_MEASUREMENTS,
)


logger = logging.getLogger()


# à modifier
def get_prefix_from_ip(addr: str):
    """from an ip addr return /24 prefix"""
    prefix = addr.split(".")[:-1]
    prefix.append("0")
    prefix = ".".join(prefix)
    return prefix


# Represents
class CBG:

    def __init__(
        self,
        ripe_credentials: dict,
    ) -> None:
        self.account = ripe_credentials["username"]
        self.key = ripe_credentials["key"]
        self.driver = RIPEAtlas(self.account, self.key)

    # Return a list (with length nb_targets) of targets with the same prefix than the target_prefix, using ...
    def get_target_hitlist(
        self, target_prefix: str, nb_targets: int, targets_per_prefix: dict
    ) -> list:
        """_summary_

        Args:
            target_prefix (str): _description_
            nb_targets (int): _description_
            targets_per_prefix (dict): _description_

        Returns:
            list: _description_
        """
        target_addr_list = []
        try:
            # get targets from a prefix and the dict
            target_addr_list = targets_per_prefix[target_prefix]
        except KeyError:
            pass

        # remove duplicated targets (and change the order)
        target_addr_list = list(set(target_addr_list))

        # if there is not enough targets associated with this prexif:
        # add random targets of the network with the same prefix
        if len(target_addr_list) < nb_targets:
            prefix = IPv4Network(target_prefix + "/24")
            target_addr_list.extend(
                [
                    str(prefix[randint(1, 254)])
                    for _ in range(0, nb_targets - len(target_addr_list))
                ]
            )

        # remove the targets in excess
        if len(target_addr_list) > nb_targets:
            target_addr_list = target_addr_list[:nb_targets]

        # fonction possible pour ajuster la taille
        return target_addr_list

    # For each prefix in the target_prefixes, probe several associated target addresses from the vantage points in vps.
    # Return measurements'ids of the probes, and the necessary time for doing all the measures.
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
        # quelle forme  de commentaires je garde ?

        active_measurements = []
        all_measurement_ids = []
        start_time = time.time()
        for _, target_prefix in enumerate(target_prefixes):
            # for target_prefix in target_prefixes:
            # get the list of target addresses from the target prefix
            target_addr_list = self.get_target_hitlist(
                target_prefix, nb_targets, targets_per_prefix
            )
            # list of all vps'ids except the targets
            vp_ids = [vps[vp_addr]["id"]
                      for vp_addr in vps if vp_addr not in target_addr_list]
            logger.debug(
                f"starting measurement for {target_prefix} with {[addr for addr in target_addr_list]}"
            )
            # c'est quoi le f là ?
            # probe all the targets and updtae the measurement results lists
            for target_addr in target_addr_list:
                for i in range(0, len(vp_ids), MAX_NUMBER_OF_VPS):
                    subset_vp_ids = vp_ids[i: i + MAX_NUMBER_OF_VPS]

                    logger.debug(
                        f"starting measurement for {target_addr} with {len(subset_vp_ids)} vps"
                    )

                    if not dry_run:
                        measurement_id = self.driver.probe(
                            str(target_addr), subset_vp_ids, str(
                                tag), nb_packets
                        )
                    else:
                        measurement_id = 404

                    active_measurements.append(measurement_id)
                    all_measurement_ids.append(measurement_id)

                    # check number of parallel measurements in not too high
                    # fonction pour ça ?
                    if len(active_measurements) >= NB_MAX_CONCURRENT_MEASUREMENTS:
                        logger.info(
                            f"Reached limit for number of concurrent measurements: {len(active_measurements)}"
                        )
                        tmp_measurement_ids = copy(active_measurements)
                        for id in tmp_measurement_ids:
                            # wait for the last measurement of the batch to end before starting a new one
                            if not dry_run:
                                measurement_result = self.driver._wait_for(id)
                                # attention, measurement_id est un dict et pas un booléen
                                if measurement_result:
                                    active_measurements.remove(id)
                            else:
                                active_measurements.remove(id)
                                time.sleep(0.5)

        logger.info(f"measurement : {tag} done")
        end_time = time.time()
        return all_measurement_ids, start_time, end_time

    # Probe targets from the vantage points in vps.
    # Return measurements'ids of the probes, and the necessary time for doing all the measures.
    def target_probing(
        self,
        targets: list,
        vps: dict,
        tag: str,
        nb_packets: int = NB_PACKETS,
        dry_run: bool = False,
    ) -> dict:
        """from a list of prefixes, start measurements for n target addrs in prefix"""

        active_measurements = []
        all_measurement_ids = []
        start_time = time.time()
        # vp_ids = [vps[vp_addr]["id"] for vp_addr in vps if vp_addr not in targets]
        for _, target_addr in enumerate(targets):
            # for target_addr in targets:
            # get vps id for measurement, remove target if in vps
            vp_ids = [vps[vp_addr]["id"]
                      for vp_addr in vps if vp_addr != target_addr]

            for i in range(0, len(vp_ids), MAX_NUMBER_OF_VPS):
                subset_vp_ids = vp_ids[i: i + MAX_NUMBER_OF_VPS]

                logger.debug(
                    f"starting measurement for {target_addr} with {len(subset_vp_ids)} vps"
                )

                if not dry_run:
                    measurement_id = self.driver.probe(
                        str(target_addr), subset_vp_ids, str(tag), nb_packets
                    )
                else:
                    measurement_id = 404

                active_measurements.append(measurement_id)
                all_measurement_ids.append(measurement_id)

                # check number of parallel measurements in not too high
                if len(active_measurements) >= NB_MAX_CONCURRENT_MEASUREMENTS:
                    logger.info(
                        f"Reached limit for number of concurrent measurements: {len(active_measurements)}"
                    )
                    tmp_measurement_ids = copy(active_measurements)
                    for id in tmp_measurement_ids:
                        # wait for the last measurement of the batch to end before starting a new one
                        if not dry_run:
                            measurement_result = self.driver._wait_for(id)
                            if measurement_result:
                                active_measurements.remove(id)
                        else:
                            active_measurements.remove(id)
                            time.sleep(0.5)

        logger.info(f"measurement : {tag} done")
        end_time = time.time()
        return all_measurement_ids, start_time, end_time

    # Probe a specific target_addr from vantage points identified by vp_ids
    # Return lists of active_measurements and all_measurements_ids
    # A functionnality is added to regulate the number of simultaneous measurements

    def address_probing(
            self,
            target_addr,
            vp_ids: list,
            active_measurements: list,
            all_measurement_ids: list,
            tag: str,
            nb_packets: int = NB_PACKETS,
            dry_run: bool = False,
    ):
        # divide the vantage points in subsets because the number of vps for one probe is limited.
        for i in range(0, len(vp_ids), MAX_NUMBER_OF_VPS):
            subset_vp_ids = vp_ids[i: i + MAX_NUMBER_OF_VPS]

            logger.debug(
                f"starting measurement for {target_addr} with {len(subset_vp_ids)} vps"
            )

            if not dry_run:
                # c'est quoi dry_run ?
                # probe the target address from the vp subset with nb_packets
                measurement_id = self.driver.probe(
                    str(target_addr), subset_vp_ids, str(tag), nb_packets
                )
            else:
                measurement_id = 404

            # update the state of measurements
            active_measurements.append(measurement_id)
            all_measurement_ids.append(measurement_id)

            # check that number of parallel measurements in not too high
            # fonction pour ça ?
            if len(active_measurements) >= NB_MAX_CONCURRENT_MEASUREMENTS:
                logger.info(
                    f"Reached limit for number of concurrent measurements: {len(active_measurements)}"
                )
                tmp_measurement_ids = copy(active_measurements)
                for id in tmp_measurement_ids:
                    # wait for the last measurement of the batch to end before starting a new one
                    if not dry_run:
                        measurement_result = self.driver._wait_for(id)
                        # attention, measurement_id est un dict et pas un booléen
                        if measurement_result:
                            active_measurements.remove(id)
                    else:
                        active_measurements.remove(id)
                        time.sleep(0.5)
        return active_measurements, all_measurement_ids

    def target_probing2(
        self,
        targets: list,
        active_measurements: list,
        all_measurement_ids: list,
        vps: dict,
        tag: str,
    ) -> dict:

        vp_ids = [vps[vp_addr]["id"]
                  for vp_addr in vps if vp_addr not in targets]

        for target_addr in targets:
            active_measurements, all_measurement_ids = self.address_probing(
                target_addr, vp_ids, active_measurements, all_measurement_ids, tag)

        logger.info(f"measurement : {tag} done")
        return active_measurements, all_measurement_ids

    def prefix_probing2(
        self,
        target_prefixes: list,
        vps: dict,
        targets_per_prefix: dict,
        tag: str,
        nb_targets: int = NB_TARGETS_PER_PREFIX,
    ) -> dict:

        active_measurements = []
        all_measurement_ids = []
        start_time = time.time()

        for target_prefix in target_prefixes:
            target_addr_list = self.get_target_hitlist(
                target_prefix, nb_targets, targets_per_prefix)
            vp_ids = [vps[vp_addr]["id"]
                      for vp_addr in vps if vp_addr not in target_addr_list]

            logger.debug(
                f"starting measurement for {target_prefix} with {[addr for addr in target_addr_list]}"
            )

            active_measurements, all_measurement_ids = self.target_probing2(
                target_addr_list, active_measurements, all_measurement_ids, vps, tag)

        logger.info(f"measurement : {tag} done")

        end_time = time.time()
        total_time = end_time - start_time
        return all_measurement_ids, total_time
