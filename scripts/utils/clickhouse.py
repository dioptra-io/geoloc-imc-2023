"""clickhouse client"""
import subprocess

from clickhouse_driver import Client 

from logger import logger

from default import (
    CLICKHOUSE_HOST,
    CLICKHOUSE_DB,
    CLICKHOUSE_USER,
    CLICKHOUSE_PASSWORD,
)

class Clickhouse():
    def __init__(
        self,
        host : str = CLICKHOUSE_HOST,
        database: str = CLICKHOUSE_DB,
        user: str = CLICKHOUSE_USER,
        password: str = CLICKHOUSE_PASSWORD,
    ) -> None:
        self.host = host
        self.database = database
        self.user = user
        self.password = password

        self.client: Client = Client(
            host = self.host,
            user = self.user,
            password = self.password
        )

        self.settings = {"max_block_size": 100000}

    # TODO: find why filter are failing
    def get_min_rtt_per_src_dst_query(self, table, filter=None, threshold=10000):
        return f"""
        WITH  arrayMin(groupArray(`min`)) as min_rtt
        SELECT IPv4NumToString(dst), IPv4NumToString(src), min_rtt
        FROM {self.database}.{table}
        WHERE `min` > -1 AND `min`< {threshold} AND dst != src
        GROUP BY (dst, src)
        """

    def get_min_rtt_per_src_dst_prefix_query(self, table, filter=None, threshold=10000):
        return f"""
        WITH  arrayMin(groupArray(`min`)) as min_rtt
        SELECT IPv4NumToString(dst_prefix), IPv4NumToString(src), min_rtt
        FROM {self.database}.{table}
        WHERE `min` > -1 AND `min`< {threshold}
        AND dst_prefix != toIPv4(substring(cutIPv6(IPv4ToIPv6(src), 0, 1), 8))
        -- {filter} -> filter not good 
        GROUP BY dst_prefix, src
        """

    def execute_iter(self, query: str) -> None:
        """use clickhouse driver instead of subprocess"""
        logger.info(f"query: {query}")
        return self.client.execute_iter(query, settings=self.settings)

    
    def execute(self,query: str) -> None:
        """execute the loaded query"""
        cmd = [
            "clickhouse-client", 
            f"--host={self.host}", 
            f"--username={self.user}",
            f"--password={self.password}",
            f"--query={query}",
        ]

        logger.info(f"executing query: {cmd}")

        # execute clickhouse process with query, TOOD: add settings
        process = subprocess.Popen(cmd)
        process.wait()
        logger.info(f"query output: {process.stdout}")


    def create_anchors_meshed_pings_table()-> None:
        pass

# def insert_results
# def create_tables

# DESCRIBE TABLE anchors_meshed_pings

# Query id: d1f084bf-9b0b-49a0-881c-839d6f7eab61

# ┌─name───┬─type───────────┬─default_type─┬─default_expression─┬─comment─┬─codec_expression─┬─ttl_expression─┐
# │ src    │ IPv4           │              │                    │         │                  │                │
# │ dst    │ IPv4           │              │                    │         │                  │                │
# │ prb_id │ UInt32         │              │                    │         │                  │                │
# │ date   │ DateTime       │              │                    │         │                  │                │
# │ sent   │ UInt32         │              │                    │         │                  │                │
# │ rcvd   │ UInt32         │              │                    │         │                  │                │
# │ rtts   │ Array(Float64) │              │                    │         │                  │                │
# │ min    │ Float64        │              │                    │         │                  │                │
# │ mean   │ Float64        │              │                    │         │                  │                │
# │ msm_id │ UInt64         │              │                    │         │                  │                │
# │ proto  │ UInt8          │              │                    │         │                  │                │
# └────────┴────────────────┴──────────────┴────────────────────┴─────────┴──────────────────┴────────────────┘

    def create_anchors_meshed_traceroutes_table()-> None:
        pass

# DESCRIBE TABLE anchors_meshed_traceroutes

# Query id: 60dd5ff3-2cf5-438c-a378-798c339d3ae1

# ┌─name───────┬─type────────────┬─default_type─┬─default_expression─┬─comment─┬─codec_expression─┬─ttl_expression─┐
# │ src_ip     │ String          │              │                    │         │                  │                │
# │ dst_prefix │ String          │              │                    │         │                  │                │
# │ dst_ip     │ String          │              │                    │         │                  │                │
# │ reply_ip   │ String          │              │                    │         │                  │                │
# │ proto      │ Int16           │              │                    │         │                  │                │
# │ hop        │ Int16           │              │                    │         │                  │                │
# │ rtt        │ Float64         │              │                    │         │                  │                │
# │ ttl        │ Int16           │              │                    │         │                  │                │
# │ prb_id     │ Int64           │              │                    │         │                  │                │
# │ msm_id     │ Int64           │              │                    │         │                  │                │
# │ timestamp  │ DateTime('UTC') │              │                    │         │                  │                │
# └────────────┴─────────────────┴──────────────┴────────────────────┴─────────┴──────────────────┴────────────────┘

    def create_anchors_to_prefix_pings_table() -> None:
        pass

# DESCRIBE TABLE anchors_to_prefix_pings

# Query id: 03d8c9c5-7d50-46dc-8767-746a33efb2f7

# ┌─name───────┬─type───────────┬─default_type─┬─default_expression───────────────────────────────────┬─comment─┬─codec_expression─┬─ttl_expression─┐
# │ src        │ IPv4           │              │                                                      │         │                  │                │
# │ dst        │ IPv4           │              │                                                      │         │                  │                │
# │ dst_prefix │ IPv4           │ MATERIALIZED │ toIPv4(substring(cutIPv6(IPv4ToIPv6(dst), 0, 1), 8)) │         │                  │                │
# │ prb_id     │ UInt32         │              │                                                      │         │                  │                │
# │ date       │ DateTime       │              │                                                      │         │                  │                │
# │ sent       │ UInt32         │              │                                                      │         │                  │                │
# │ rcvd       │ UInt32         │              │                                                      │         │                  │                │
# │ rtts       │ Array(Float64) │              │                                                      │         │                  │                │
# │ min        │ Float64        │              │                                                      │         │                  │                │
# │ mean       │ Float64        │              │                                                      │         │                  │                │
# │ msm_id     │ UInt64         │              │                                                      │         │                  │                │
# │ proto      │ UInt8          │              │                                                      │         │                  │                │
# └────────────┴────────────────┴──────────────┴──────────────────────────────────────────────────────┴─────────┴──────────────────┴────────────────┘

    def create_ping_10k_to_anchors_table()-> None:
        pass

# DESCRIBE TABLE ping_10k_to_anchors

# Query id: 8eff1546-3ec9-48ef-b9da-1646931b40ae

# ┌─name───┬─type───────────┬─default_type─┬─default_expression─┬─comment─┬─codec_expression─┬─ttl_expression─┐
# │ src    │ IPv4           │              │                    │         │                  │                │
# │ dst    │ IPv4           │              │                    │         │                  │                │
# │ prb_id │ UInt32         │              │                    │         │                  │                │
# │ date   │ DateTime       │              │                    │         │                  │                │
# │ sent   │ UInt32         │              │                    │         │                  │                │
# │ rcvd   │ UInt32         │              │                    │         │                  │                │
# │ rtts   │ Array(Float64) │              │                    │         │                  │                │
# │ min    │ Float64        │              │                    │         │                  │                │
# │ mean   │ Float64        │              │                    │         │                  │                │
# │ msm_id │ UInt64         │              │                    │         │                  │                │
# │ proto  │ UInt8          │              │                    │         │                  │                │
# └────────┴────────────────┴──────────────┴────────────────────┴─────────┴──────────────────┴────────────────┘


    def create_probes_to_prefix_pings_table()-> None:
        pass

# DESCRIBE TABLE probes_to_prefix_pings

# Query id: ab4d50c8-c4ad-4abc-9c61-42e782fa0c2c

# ┌─name───────┬─type───────────┬─default_type─┬─default_expression───────────────────────────────────┬─comment─┬─codec_expression─┬─ttl_expression─┐
# │ src        │ IPv4           │              │                                                      │         │                  │                │
# │ dst        │ IPv4           │              │                                                      │         │                  │                │
# │ dst_prefix │ IPv4           │ MATERIALIZED │ toIPv4(substring(cutIPv6(IPv4ToIPv6(dst), 0, 1), 8)) │         │                  │                │
# │ prb_id     │ UInt32         │              │                                                      │         │                  │                │
# │ date       │ DateTime       │              │                                                      │         │                  │                │
# │ sent       │ UInt32         │              │                                                      │         │                  │                │
# │ rcvd       │ UInt32         │              │                                                      │         │                  │                │
# │ rtts       │ Array(Float64) │              │                                                      │         │                  │                │
# │ min        │ Float64        │              │                                                      │         │                  │                │
# │ mean       │ Float64        │              │                                                      │         │                  │                │
# │ msm_id     │ UInt64         │              │                                                      │         │                  │                │
# │ proto      │ UInt8          │              │                                                      │         │                  │                │
# └────────────┴────────────────┴──────────────┴──────────────────────────────────────────────────────┴─────────┴──────────────────┴────────────────┘

    def create_targets_to_landmarks_pings_table()-> None:
        pass


# DESCRIBE TABLE targets_to_landmarks_pings

# Query id: d982d86e-a6b5-4de4-88e2-cdf434c9eb20

# ┌─name───────┬─type───────────┬─default_type─┬─default_expression───────────────────────────────────┬─comment─┬─codec_expression─┬─ttl_expression─┐
# │ src        │ IPv4           │              │                                                      │         │                  │                │
# │ dst        │ IPv4           │              │                                                      │         │                  │                │
# │ dst_prefix │ IPv4           │ MATERIALIZED │ toIPv4(substring(cutIPv6(IPv4ToIPv6(dst), 0, 1), 8)) │         │                  │                │
# │ prb_id     │ UInt32         │              │                                                      │         │                  │                │
# │ date       │ DateTime       │              │                                                      │         │                  │                │
# │ sent       │ UInt32         │              │                                                      │         │                  │                │
# │ rcvd       │ UInt32         │              │                                                      │         │                  │                │
# │ rtts       │ Array(Float64) │              │                                                      │         │                  │                │
# │ min        │ Float64        │              │                                                      │         │                  │                │
# │ mean       │ Float64        │              │                                                      │         │                  │                │
# │ msm_id     │ UInt64         │              │                                                      │         │                  │                │
# │ proto      │ UInt8          │              │                                                      │         │                  │                │
# └────────────┴────────────────┴──────────────┴──────────────────────────────────────────────────────┴─────────┴──────────────────┴────────────────┘




