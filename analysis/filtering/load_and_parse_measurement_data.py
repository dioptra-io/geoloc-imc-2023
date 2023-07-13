import json
import pickle
import argparse

from collections import defaultdict, OrderedDict
from pathlib import Path

from geoloc_imc_2023.measurement_utils import load_measurement_results, save_data
from geoloc_imc_2023.default import (
    REMOVED_PROBES,
    ANCHOR_TARGET_ALL_VP,
    ANCHOR_TARGET_ANCHOR_VP,
    ANCHOR_TARGET_PROBE_VP,
    ANCHORS_MESHED_PING_TABLE,
    PROBES_TO_ANCHORS_PING_TABLE,
    DB_HOST,
    GEO_REPLICATION_DB,
)
from clickhouse_driver import Client


def get_data_from_clickhouse(database, table, filter=None, threshold=10000):
    query = (
        f"SELECT IPv4NumToString(dst), groupArray((IPv4NumToString(src), `rtts`))"
        f"FROM {database}.{table} "
        f"WHERE `min` > -1 AND `min`< {threshold} {filter} "
        f"GROUP BY dst"
    )
    return query


def load_removed_probes() -> dict:
    """load all geolocated disputed probes"""
    with open(REMOVED_PROBES, "r") as f:
        return json.load(f)


def load_measurement_from_clickhouse(table: str) -> dict:
    """load an parse measurements from clickhouse"""
    # get data from clickhouse
    removed_probes = load_removed_probes()

    in_clause = f"".join([f",toIPv4('{p}')" for p in removed_probes])[1:]
    filter = f"AND dst not in ({in_clause}) AND src not in ({in_clause}) "

    query = get_data_from_clickhouse(GEO_REPLICATION_DB, table, filter=filter)

    client = Client(DB_HOST)

    settings = {"max_block_size": 100000}
    rows = client.execute_iter(query, settings=settings)

    # parse clickhouse data
    measurement_results = defaultdict(dict)
    for row in rows:
        dst = row[0]

        for vp, rtt_list in row[1]:

            if vp == dst:
                continue

            min_rtt = min(rtt_list)
            measurement_results[dst][vp] = {"min_rtt": min_rtt, "rtt_list": rtt_list}
        
        measurement_results[target] = OrderedDict(
            {
                vp: results
                for vp, results in sorted(
                    measurement_results[target].items(),
                    key=lambda item: item[1]["min_rtt"],
                )
            }
        )

    return measurement_results


if __name__ == "__main__":
    # parse cmd line arguments
    # parser = argparse.ArgumentParser()
    # parser.add_argument(
    #     "--table_name", help="clichouse table for measurement data", type=str
    # )

    # table = parser.table_name

    table = ANCHOR_TARGET_ALL_VP

    if table == ANCHORS_MESHED_PING_TABLE:
        out_file = ANCHOR_TARGET_ANCHOR_VP
    elif table == PROBES_TO_ANCHORS_PING_TABLE:
        out_file = ANCHOR_TARGET_PROBE_VP
    elif table == ANCHOR_TARGET_ALL_VP:

        anchor_target_to_anchor_vp_results = load_measurement_results(
            ANCHOR_TARGET_ANCHOR_VP
        )
        anchor_target_to_probe_vp_results = load_measurement_results(
            ANCHOR_TARGET_PROBE_VP
        )

        anchor_target_all_vp_results = {}
        for target in anchor_target_to_probe_vp_results:
            anchor_target_all_vp_results[target] = anchor_target_to_probe_vp_results[
                target
            ]

            anchor_target_all_vp_results[target].update(
                anchor_target_to_anchor_vp_results[target]
            )

        save_data(ANCHOR_TARGET_ALL_VP, anchor_target_all_vp_results)

    else:
        raise RuntimeError(
            f"table unknown, tables are: {PROBES_TO_ANCHORS_PING_TABLE} | {ANCHORS_MESHED_PING_TABLE}"
        )

    measurement_results = load_measurement_from_clickhouse(table)

    save_data(out_file, measurement_results)

