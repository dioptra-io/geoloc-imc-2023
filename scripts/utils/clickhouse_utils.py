# Functions to query a clickhouse database

# the filter contains all the invalid probes that sould not be considerer.
# the treshold is the maximal rtt allowed.

def get_min_rtt_per_src_dst_query_ping_table(database, table, filter=None, threshold=10000):
    query = (
        f"WITH  arrayMin(groupArray(`min`)) as min_rtt "
        f"SELECT IPv4NumToString(dst), IPv4NumToString(src), min_rtt "
        f"FROM {database}.{table} "
        f"WHERE `min` > -1 AND `min`< {threshold} AND dst != src {filter} "
        f"GROUP BY dst, src "
    )
    return query


def get_min_rtt_per_src_dst_prefix_query_ping_table(database, table, filter=None, threshold=10000):
    query = (
        f"WITH  arrayMin(groupArray(`min`)) as min_rtt "
        f"SELECT IPv4NumToString(dst_prefix), IPv4NumToString(src), min_rtt "
        f"FROM {database}.{table} "
        f"WHERE `min` > -1 AND `min`< {threshold} "
        f"AND dst_prefix != toIPv4(substring(cutIPv6(IPv4ToIPv6(src), 0, 1), 8)) "
        f"{filter} "
        f"GROUP BY dst_prefix, src "
    )
    return query
