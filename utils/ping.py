import logging
import time

from copy import copy

from utils.atlas_api import RIPEAtlas, wait_for
from utils.geoloc_earth import get_target_hitlist
from default import (NB_PACKETS, NB_TARGETS_PER_PREFIX,
                     MAX_NUMBER_OF_VPS, NB_MAX_CONCURRENT_MEASUREMENTS)


class PING:
    def __init__(
        self,
        ripe_credentials: dict,
    ) -> None:
        self.account = ripe_credentials["username"]
        self.key = ripe_credentials["key"]
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
        for _, target_prefix in enumerate(target_prefixes):
            # get target_addr_list
            target_addr_list = get_target_hitlist(
                target_prefix, nb_targets, targets_per_prefix
            )

            vp_ids = [
                vps[vp_addr]["address_v4"] for vp_addr in vps if vp_addr not in target_addr_list
            ]

            logging.debug(
                f"starting measurement for {target_prefix} with {[addr for addr in target_addr_list]}"
            )

            for target_addr in target_addr_list:
                for i in range(0, len(vp_ids), MAX_NUMBER_OF_VPS):
                    subset_vp_ids = vp_ids[i: i + MAX_NUMBER_OF_VPS]

                    logging.debug(
                        f"starting measurement for {target_addr} with {len(subset_vp_ids)} vps"
                    )

                    if not dry_run:
                        measurement_id = self.driver.ping(
                            str(target_addr), subset_vp_ids, str(
                                tag), nb_packets
                        )
                    else:
                        measurement_id = 404

                    active_measurements.append(measurement_id)
                    all_measurement_ids.append(measurement_id)

                    # check number of parallel measurements in not too high
                    if len(active_measurements) >= NB_MAX_CONCURRENT_MEASUREMENTS:
                        logging.info(
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

        logging.info(f"measurement : {tag} done")

        end_time = time.time()

        return all_measurement_ids, start_time, end_time

    def ping_by_target(
        self,
        targets: list,
        vps: dict,
        tag: str,
        nb_packets: int = NB_PACKETS,
        dry_run: bool = False,
    ):
        """from a list of prefixes, start measurements for n target addrs in prefix"""

        active_measurements = []
        all_measurement_ids = []
        start_time = time.time()
        for _, target_addr in enumerate(targets):
            # get vps id for measurement, remove target if in vps
            vp_ids = [vps[vp_addr]["address_v4"]
                      for vp_addr in vps if vp_addr != target_addr]

            for i in range(0, len(vp_ids), MAX_NUMBER_OF_VPS):
                subset_vp_ids = vp_ids[i: i + MAX_NUMBER_OF_VPS]

                logging.debug(
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

                # check number of parallel measurements in not too high
                if len(active_measurements) >= NB_MAX_CONCURRENT_MEASUREMENTS:
                    logging.info(
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

        logging.info(f"measurement : {tag} done")

        end_time = time.time()

        return all_measurement_ids, start_time, end_time
