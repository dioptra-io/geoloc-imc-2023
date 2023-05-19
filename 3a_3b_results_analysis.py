import random
import pickle
import argparse
import logging
import numpy as np

from pathlib import Path

from geoloc_imc_2023.measurement_utils import (
    load_atlas_anchors,
    load_all_atlas_probes,
    save_data,
)
from geoloc_imc_2023.helpers import select_best_guess_centroid, haversine
from geoloc_imc_2023.query_api import get_measurements_from_tag

from geoloc_imc_2023.default import (
    ANCHOR_TARGET_ALL_VP,
    ANCHOR_TARGET_PROBE_VP_RESULT_FILE,
)

NB_TRIAL = 100
STEP = 1000

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


def load_measurement_results(in_file: Path) -> dict:
    """get measuerments from local pickle file"""
    with open(in_file, "rb") as f:
        return pickle.dump(in_file)


def get_results_from_set(target_addr: str, vp_set: set, target_results: dict) -> dict:
    measurement_set = {}
    for vp in vp_set:
        # just in case
        if vp == target_addr:
            continue

        # some targets might not have vps in their result
        try:
            measurement_set[vp] = target_results[vp]
        except KeyError:
            continue

    return measurement_set


def get_shortest_ping_result(measurement_set: dict) -> tuple:
    """return the position of the vantage point with shortest ping measurement"""
    # TODO get ordered rtts
    shortest_ping = float("inf")
    closest_vp = None
    for vp, result in measurement_set.items():
        if shortest_ping > result["min_rtt"]:
            shortest_ping = result["min_rtt"]
            closest_vp = vp

    return closest_vp, shortest_ping


def get_dst_error(
    vp_subset: set, measurement_results: dict, target_dataset: dict, vp_dataset: dict
) -> list:
    """from a set of measurement return shortest Ping and CBG distance error"""

    cbg_d_error_list = []
    shortest_ping_d_error_list = []

    for target_addr in measurement_results:

        target_results = measurement_results[target_addr]
        measurement_set = get_results_from_set(target_addr, vp_subset, target_results)

        # in case no measurement from vp set for target
        if measurement_set:
            intersection, centroid = select_best_guess_centroid(
                measurement_set, vp_dataset
            )
            # get from clickhouse
            closest_vp, min_rtt = get_shortest_ping_result(measurement_set)

            # compute distance error
            try:
                dst_error = haversine(
                    (
                        target_dataset[target_addr]["latitude"],
                        target_dataset[target_addr]["longitude"],
                    ),
                    centroid,
                )

                cbg_d_error_list.append(dst_error)

                # shortest ping
                dst_error = haversine(
                    (
                        target_dataset[target_addr]["latitude"],
                        target_dataset[target_addr]["longitude"],
                    ),
                    (
                        vp_dataset[closest_vp]["latitude"],
                        vp_dataset[closest_vp]["longitude"],
                    ),
                )
                shortest_ping_d_error_list.append(dst_error)
            except KeyError as e:
                continue

    return (cbg_d_error_list, shortest_ping_d_error_list)


def load_cache_results(result_file: Path, smallest_subset: int = 10) -> dict:
    """return already analyzed measurement results"""
    # result_path = DATA_PATH / "figure_3a_3b_anchor_target_probe_vp.pickle"
    try:
        with open(result_file, "rb") as f:
            result_analysis = pickle.load(f)
        last_subset = max([subset_size for subset_size in result_analysis["cbg"]])

    except FileNotFoundError:
        logger.error("no results files")
        result_analysis = {"cbg": {}, "shortest_ping": {}}
        last_subset = smallest_subset

    return result_analysis, last_subset


def analyze_results(out_file: Path, measurement_results, vp_dataset, target_dataset) -> None:
    """analyze measurement results"""

    result_analysis, last_subset = load_cache_results(out_file)

    cbg_results = result_analysis["cbg"]
    shortest_ping_results = result_analysis["shortest_ping"]

    print("last subset analyzed:", last_subset)

    for vp_set_size in range(last_subset, len(vp_dataset), STEP):

        subset_median_cbg = []
        subset_median_shortest_ping = []

        all_dst_errors_cbg = []
        all_dst_errors_shortest_ping = []

        # remove initial step so data are aligned with step
        if last_subset == 10:
            if vp_set_size != 10:
                vp_set_size -= 10

        print("vp subset size:", vp_set_size)

        for index_trial in range(0, NB_TRIAL):

            # get vp set
            pool = tuple(vp_dataset)
            n = len(pool)
            indices = sorted(random.sample(range(n), vp_set_size))
            vp_subset = tuple(pool[i] for i in indices)

            # TODO: check validity of vp set (geolocation, diversity)
            cbg_dst_errors_list, shortest_ping_dst_errors_list = get_dst_error(
                vp_subset=vp_subset,
                measurement_results=measurement_results,
                target_dataset=target_dataset,
                vp_dataset=vp_dataset,
            )

            subset_median_cbg.append(np.median(cbg_dst_errors_list))
            subset_median_shortest_ping.append(np.median(shortest_ping_dst_errors_list))

            all_dst_errors_cbg.extend(cbg_dst_errors_list)
            all_dst_errors_shortest_ping.extend(shortest_ping_dst_errors_list)

            index_trial += 1

        median_error_cbg = np.median(subset_median_cbg)
        median_error_shortest_ping = np.median(subset_median_shortest_ping)

        # get the standard deviation over all trials
        deviation_cbg = np.std(subset_median_cbg)
        deviation_shortest_ping = np.std(subset_median_shortest_ping)

        cbg_results[vp_set_size] = {
            "median_error": median_error_cbg,
            "deviation": deviation_cbg,
            "data": all_dst_errors_cbg,
        }
        shortest_ping_results[vp_set_size] = {
            "median_error": median_error_shortest_ping,
            "deviation": deviation_shortest_ping,
            "data": all_dst_errors_shortest_ping,
        }

        result_analysis["cbg"].update(cbg_results)
        result_analysis["shortest_ping"].update(cbg_results)

        save_data(out_file, result_analysis)

        print(f"subset size: {vp_set_size} done.")
        print(f"median cbg = {median_error_cbg} | std cbg = {deviation_cbg}")
        print(
            f"median shortest_ping = {median_error_shortest_ping} | std shortest_ping = {deviation_shortest_ping}"
        )


if __name__ == "__main__":

    # load results
    with open(ANCHOR_TARGET_ALL_VP, "rb") as f:
        measurement_results = pickle.load(f)

    print("Total number of targets measured:", len(measurement_results))

    # load vps and targets dataset (here only anchors)
    target_dataset = load_atlas_anchors()
    vp_dataset = load_all_atlas_probes()

    target_unknown = set()
    vp_unknown = set()
    for target in measurement_results:
        try:
            target_dataset[target]
        except KeyError:
            target_unknown.add(target)
        for vp in measurement_results[target]:
            try:
                vp_dataset[vp]
            except KeyError:
                vp_unknown.add(vp)

    print("nb targets:", len(target_dataset))
    print("nb vps:", len(vp_dataset))

    print("target unknown:", len(target_unknown))
    print("vp unknown:", len(vp_unknown))

    analyze_results(
        out_file= ANCHOR_TARGET_PROBE_VP_RESULT_FILE, 
        vp_dataset=vp_dataset,
        target_dataset=target_dataset,
        measurement_results=measurement_results
    )
