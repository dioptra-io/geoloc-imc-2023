# Two classes to instantiate before calling RIPE Atlas API: one for ping measurements and one for traceroute measurements

import time

from pprint import pprint
from copy import copy

from logger import logger
from scripts.ripe_atlas.atlas_api import RIPEAtlas, wait_for, get_target_hitlist
from scripts.utils.credentials import get_ripe_atlas_credentials


MAX_NUMBER_OF_VPS = 1_000
NB_MAX_CONCURRENT_MEASUREMENTS = 90
NB_PACKETS = 3
NB_TARGETS_PER_PREFIX = 3


class PING:
    def __init__(
        self,
    ) -> None:
        ripe_credentials = get_ripe_atlas_credentials()

        self.account = ripe_credentials["username"]
        self.key = ripe_credentials["secret_key"]

        self.driver = RIPEAtlas(self.account, self.key)

    def ping_by_prefix(
        self,
        target_prefixes: list,
        vps: dict,
        targets_per_prefix: dict,
        tag: str,
        nb_packets: int = NB_PACKETS,
        nb_targets: int = NB_TARGETS_PER_PREFIX,
        dry_run: bool = False,
    ):
        """from a list of prefixes, start measurements for n target addrs in prefix"""

        active_measurements = []
        all_measurement_ids = []
        start_time = time.time()
        for i, target_prefix in enumerate(target_prefixes):

            logger.info(
                f"Ping for target prefix:: {target_prefix}, {i+1}/{len(target_prefixes)}"
            )

            # get target_addr_list
            target_addr_list = get_target_hitlist(
                target_prefix, nb_targets, targets_per_prefix
            )

            # get vps id for measurement, remove target if in vps

            logger.debug(
                f"starting measurement for {target_prefix} with {[addr for addr in target_addr_list]}"
            )

            for target_addr in target_addr_list:
                vp_ids = [vp["id"] for vp in vps if vp["address_v4"] != target_addr]
                for i in range(0, len(vp_ids), MAX_NUMBER_OF_VPS):
                    subset_vp_ids = vp_ids[i : i + MAX_NUMBER_OF_VPS]

                    logger.debug(
                        f"starting measurement for {target_addr} with {len(subset_vp_ids)} vps"
                    )

                    if not dry_run:
                        measurement_id = self.driver.ping(
                            str(target_addr), subset_vp_ids, str(tag), nb_packets
                        )

                        logger.info(
                            f"measurement tag: {tag} : started measurement id : {measurement_id}"
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
                                measurement_result = wait_for(id)
                                if measurement_result:
                                    active_measurements.remove(id)
                            else:
                                active_measurements.remove(id)
                                time.sleep(0.5)

        logger.info(f"measurement : {tag} done")

        end_time = time.time()

        return all_measurement_ids, start_time, end_time

    def ping_by_target(
        self,
        targets: list[dict],
        vps: list[dict],
        tag: str,
        nb_packets: int = NB_PACKETS,
        dry_run: bool = False,
    ):
        """from a list of prefixes, start measurements for n target addrs in prefix"""

        active_measurements = []
        all_measurement_ids = []
        start_time = time.time()
        for i, target_addr in enumerate(targets):
            logger.info(f"Ping for target:: {target_addr}, {i+1}/{len(targets)}")

            # get vps id for measurement, remove target if in vps
            vp_ids = [vp["id"] for vp in vps if vp["address_v4"] != target_addr]

            for i in range(0, len(vp_ids), MAX_NUMBER_OF_VPS):
                subset_vp_ids = vp_ids[i : i + MAX_NUMBER_OF_VPS]

                logger.debug(
                    f"starting measurement for {target_addr} with {len(subset_vp_ids)} vps"
                )

                if not dry_run:
                    measurement_id = self.driver.ping(
                        str(target_addr), subset_vp_ids, str(tag), nb_packets
                    )
                else:
                    measurement_id = 404

                active_measurements.append(measurement_id)
                all_measurement_ids.append(measurement_id)

                logger.info(
                    f"measurement tag: {tag} : started measurement id : {measurement_id}"
                )

                # check number of parallel measurements in not too high
                if len(active_measurements) >= NB_MAX_CONCURRENT_MEASUREMENTS:
                    logger.info(
                        f"Reached limit for number of concurrent measurements: {len(active_measurements)}"
                    )
                    tmp_measurement_ids = copy(active_measurements)
                    for id in tmp_measurement_ids:
                        # wait for the last measurement of the batch to end before starting a new one
                        if not dry_run:
                            measurement_result = wait_for(id)
                            if measurement_result:
                                active_measurements.remove(id)
                        else:
                            active_measurements.remove(id)
                            time.sleep(0.5)

        logger.info(f"measurement : {tag} done")

        end_time = time.time()

        return all_measurement_ids, start_time, end_time


class TRACEROUTE:
    def __init__(
        self,
    ) -> None:
        ripe_credentials = get_ripe_atlas_credentials()

        self.account = ripe_credentials["username"]
        self.key = ripe_credentials["secret_key"]
        self.driver = RIPEAtlas(self.account, self.key)

    def traceroute(self, target, probe_id):
        description = "Geoloc project"
        tags = ["traceroute", "test", "geoloc"]
        is_public = True
        probes = {"value": str(probe_id), "type": "probes", "requested": 1}
        packets = 3
        protocol = "ICMP"
        options = (self.key, description, tags, is_public, packets, protocol)

        response = self.driver.traceroute_measurement(target, probes, options)

        if "measurements" in response and len(response["measurements"]) == 1:
            return response["measurements"][0]
        else:
            print(f"Failed to traceroute")
            pprint(response)
            return None
