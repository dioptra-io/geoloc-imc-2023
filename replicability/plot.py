from utils.utils import load_json
from replicability.globals import *
from replicability.common import compute_error_threshold_cdfs
from replicability.analysis import compute_geo_info
from plot_utils.plot import plot_multiple_cdf, homogenize_legend, plot_save, plot_multiple_error_bars
from internet_measurements_metadata.geolocation.utils import iso_code_2_to_country
from replicability.ripe_utils import download_ripe_probes
import numpy as np

def plot_error_threshold(threshold_distances, results_file, country_per_ip, vps_per_country):

    is_compute_error_a_to_a = False
    is_compute_error_p_to_a = False
    is_compute_vp_selection_algorithm = False
    is_compute_error_continent = True

    errors_threshold_anchors_to_anchors = load_json(results_file[0])
    error_threshold_cdfs_a_to_a, circles_threshold_cdfs_a_to_a, _ = \
        compute_error_threshold_cdfs(errors_threshold_anchors_to_anchors)
    if is_compute_error_a_to_a:

        Ys = error_threshold_cdfs_a_to_a
        labels = [f"{t}" for t in threshold_distances]
        fig, ax = plot_multiple_cdf(Ys, 10000, 1, 10000,
                                    "Geolocation error (km)",
                                    "CDF of targets",
                                    xscale="log",
                                    yscale="linear",
                                    legend=labels)

        homogenize_legend(ax, "lower right")
        ofile = f"resources/replicability/cbg_thresholds.pdf"
        plot_save(ofile, is_tight_layout=True)

        Ys = circles_threshold_cdfs_a_to_a
        labels = [f"{t}" for t in threshold_distances]
        fig, ax = plot_multiple_cdf(Ys, 10000, 1, max(max(Y) for Y in Ys),
                                    "Number of useful VPs",
                                    "CDF of targets",
                                    xscale="log",
                                    yscale="linear",
                                    legend=labels)

        homogenize_legend(ax, "lower right")
        ofile = f"resources/replicability/cbg_thresholds_circles.pdf"
        plot_save(ofile, is_tight_layout=True)


    """
    Look at probe 10k to anchors
    """

    if is_compute_error_p_to_a:
        print("Computing probes to anchors")
        errors_threshold_probes_to_anchors = load_json(results_file[1])
        error_threshold_cdfs_p_to_a, circles_threshold_cdfs_p_to_a, _ = compute_error_threshold_cdfs(
            errors_threshold_probes_to_anchors)

        Ys = error_threshold_cdfs_p_to_a
        print(len(error_threshold_cdfs_p_to_a[0]))
        labels = ["All VPs"]
        labels.extend([f"VPs > {t} km" for t in threshold_distances if t > 0])
        fig, ax = plot_multiple_cdf(Ys, 10000, 1, 10000,
                                    "Geolocation error (km)",
                                    "CDF of targets",
                                    xscale="log",
                                    yscale="linear",
                                    legend=labels)
        homogenize_legend(ax, "lower right", legend_size=12)
        ofile = f"resources/replicability/cbg_thresholds_probes_to_anchors.pdf"
        plot_save(ofile, is_tight_layout=True)

    # Ys = [error_threshold_cdfs_p_to_a[0], error_threshold_cdfs_a_to_a[0]]
    # labels = ["All probes", "Only anchors"]
    # fig, ax = plot_multiple_cdf(Ys, 10000, 1, 10000,
    #                             "Geolocation error (km)",
    #                             "CDF of targets",
    #                             xscale="log",
    #                             yscale="linear",
    #                             legend=labels)
    # homogenize_legend(ax, "lower right")
    # ofile = f"resources/replicability/cbg_thresholds_all.pdf"
    # plot_save(ofile, is_tight_layout=True)

    if is_compute_vp_selection_algorithm:
        Ys = []
        labels = []
        for i, file in enumerate(results_file):
            if "vp_selection_algorithm_probes" in file:
                n_vps = file.split(".json")[0].split("vp_selection_algorithm_probes_")[1]
                n_vps = int(n_vps)
                errors_threshold_vp_selection_algorithm = load_json(results_file[i])
                error_threshold_cdfs_p_to_a_vp_selection, circles_threshold_cdfs_p_to_a_vp_selection, _ = compute_error_threshold_cdfs(
                    errors_threshold_vp_selection_algorithm)
                Ys.append(list(error_threshold_cdfs_p_to_a_vp_selection[0]))
                labels.append(f"{n_vps} closest VP (RTT)")
                if n_vps == 10:
                    # Take the baseline where 10 VPs are used to geolocate a target
                    error_threshold_cdfs_p_to_a, circles_threshold_cdfs_p_to_a, _ = compute_error_threshold_cdfs(
                        errors_threshold_probes_to_anchors, errors_threshold_vp_selection_algorithm)
                    Ys.append(list(error_threshold_cdfs_p_to_a[0]))
                    labels.append("All VPs")

        fig, ax = plot_multiple_cdf(Ys, 10000, 1, 10000,
                                    "Geolocation error (km)",
                                    "CDF of targets",
                                    xscale="log",
                                    yscale="linear",
                                    legend=labels)
        homogenize_legend(ax, "lower right")
        ofile = f"resources/replicability/cbg_thresholds_vp_selection_probes.pdf"
        plot_save(ofile, is_tight_layout=True)

    """
    Plot results with fixed set of probes
    """

    # Ys = []
    # labels = []
    # for i, file in enumerate(results_file):
    #     if "fixed_set" in file:
    #         errors_threshold_fixed_set = load_json(results_file[i])
    #         error_threshold_cdfs_a_to_a_fixed_set, circles_threshold_cdfs_a_to_a_fixed_set, _ = compute_error_threshold_cdfs(
    #             errors_threshold_fixed_set)
    #         # Take the baseline where IP addresses where geolocated by the technique
    #         error_threshold_cdfs_a_to_a, circles_threshold_cdfs_a_to_a, _ = compute_error_threshold_cdfs(
    #             errors_threshold_anchors_to_anchors, errors_threshold_fixed_set)
    #         Ys.append(list(error_threshold_cdfs_a_to_a[0]))
    #         labels.append("All anchors")
    #         Ys.append(list(error_threshold_cdfs_a_to_a_fixed_set[0]))
    #         labels.append(f"Fixed set (one per city)")
    #         break
    #
    # fig, ax = plot_multiple_cdf(Ys, 10000, 1, 10000,
    #                             "Geolocation error (km)",
    #                             "CDF of targets",
    #                             xscale="log",
    #                             yscale="linear",
    #                             legend=labels)
    # homogenize_legend(ax, "lower right")
    # ofile = f"resources/replicability/cbg_thresholds_fixed_set.pdf"
    # plot_save(ofile, is_tight_layout=True)

    """
    Compute results per continent
    """
    if is_compute_error_continent:
        errors_threshold_probes_to_anchors = load_json(results_file[1])
        continent_name_by_continent_code, continent_by_iso_2, country_by_iso_2 = iso_code_2_to_country()
        _, _, error_per_ip = compute_error_threshold_cdfs(
            errors_threshold_probes_to_anchors)

        error_per_continent_cdf = {}
        error_per_country_cdf = {}

        # Match the anchors of the second replicated paper
        anchors_second = set(load_json("resources/replicability/anchors_ip_lst.json"))
        for ip, error in error_per_ip.items():
            if ip not in anchors_second:
                continue
            country = country_per_ip[ip]
            continent = continent_by_iso_2[country]
            error_per_continent_cdf.setdefault(continent, []).append(error)
            error_per_country_cdf.setdefault(country, []).append(error)

        error_per_country_cdf_med = {country_by_iso_2[x]:(np.median(error_per_country_cdf[x]),
                                                          len(error_per_country_cdf[x]), len(vps_per_country[x])) for x in error_per_country_cdf}

        error_per_country_cdf_med_sorted = sorted(error_per_country_cdf_med.items(), key=lambda x :x[1][0], reverse=True)
        print(error_per_country_cdf_med_sorted)

        Ys = [list(error_per_continent_cdf[c]) for c in error_per_continent_cdf]
        labels = [f"{c} ({len(error_per_continent_cdf[c])})" for c in error_per_continent_cdf]
        fig, ax = plot_multiple_cdf(Ys, 10000, 1, 10000,
                                    "Geolocation error (km)",
                                    "CDF of targets",
                                    xscale="log",
                                    yscale="linear",
                                    legend=labels)
        homogenize_legend(ax, "lower right")
        ofile = f"resources/replicability/cbg_thresholds_continent.pdf"
        plot_save(ofile, is_tight_layout=True)


def plot_rtt_dist_per_target_closest_probe(rtts_per_closest_probes):

    mean_cdf = []
    stddev_cdf = []

    for dst, rtt_dist in rtts_per_closest_probes.items():
        if len(rtt_dist) > 1:
            mean = np.mean(rtt_dist)
            stddev = np.std(rtt_dist)
            mean_cdf.append(mean)
            stddev_cdf.append(stddev)

    Ys = [mean_cdf, stddev_cdf]
    labels = ["Mean", "stddev"]
    fig, ax = plot_multiple_cdf(Ys, 10000, 0.1, max(max(Y) for Y in Ys),
                                "RTT Metric (ms)",
                                "CDF of targets",
                                xscale="log",
                                yscale="linear",
                                legend=labels)
    homogenize_legend(ax, "lower right")
    ofile = f"resources/replicability/rtts_per_closest_probe.pdf"
    plot_save(ofile, is_tight_layout=True)

def plot_fixed_subset(fixed_set_probes_one_per_city_file, fixed_set_probes_one_per_city_asn_file, min_rtt_per_dst_file):

    """

    Sort the min_rtt distributions per their number of RTTs under 0.4 ms
    :param fixed_set_probes_file:
    :return:
    """
    fixed_set_probes_results_per_city = load_json(fixed_set_probes_one_per_city_file)
    fixed_set_probes_results_per_city_asn = load_json(fixed_set_probes_one_per_city_asn_file)
    min_rtt_per_dst = load_json(min_rtt_per_dst_file)

    min_rtt_per_dst = {x : min_rtt_per_dst[x] for x in min_rtt_per_dst if x in fixed_set_probes_results_per_city["1"][1]}
    min_rtt_per_dst_cdf = list(min_rtt_per_dst.values())
    n_vps_per_granularity_l = [1, 10]
    Ys = [min_rtt_per_dst_cdf]
    labels = ["All VPs"]
    for n_vps_per_granularity in n_vps_per_granularity_l:
        n_vps_per_granularity = str(n_vps_per_granularity)
        vps_per_target, fixed_set_probes_results_per_city_n_vps = fixed_set_probes_results_per_city[n_vps_per_granularity]
        vps_per_target_asn, fixed_set_probes_results_per_city_asn_n_vps = fixed_set_probes_results_per_city_asn[n_vps_per_granularity]
        fixed_set_probes_results_per_city_cdf = [min(x) for x in fixed_set_probes_results_per_city_n_vps.values()]
        fixed_set_probes_results_per_city_asn_cdf = [min(x) for x in fixed_set_probes_results_per_city_asn_n_vps.values()]
        # Compute the number of VPs needed
        n_vps_used = set()
        n_vps_used_asn = set()

        for _, vps in vps_per_target.items():
            n_vps_used.update(vps)

        for _, vps in vps_per_target_asn.items():
            n_vps_used_asn.update(vps)

        # DEBUG
        # if n_vps_per_granularity == "100":
        #     for dst, rtts in fixed_set_probes_results_per_city_asn_n_vps.items():
        #         if min(rtts) > 1 and min_rtt_per_dst[dst] < 1:
        #             print(dst)
        Ys.append(fixed_set_probes_results_per_city_asn_cdf)
        labels.append(f"{n_vps_per_granularity} VP per AS/City ({len(n_vps_used_asn)})")
        Ys.append(fixed_set_probes_results_per_city_cdf)
        labels.append(f"{n_vps_per_granularity} VP per city ({len(n_vps_used)})")
    # sorted_fixed_set = sorted(fixed_set_probes_results, key=lambda x: len([y for y in x.values() if y <= 0.4]))
    #
    # top_fixed_set = list(sorted_fixed_set[-1].values())
    # bottom_fixed_set = list(sorted_fixed_set[0].values())
    # median_fixed_set = list(sorted_fixed_set[int(len(sorted_fixed_set)/2)].values())

    fig, ax = plot_multiple_cdf(Ys, 10000, 0.1, max(max(Y) for Y in Ys),
                                "Min RTT (ms)",
                                "CDF of targets",
                                xscale="log",
                                yscale="linear",
                                legend=labels)
    homogenize_legend(ax, "lower right")
    ofile = f"resources/replicability/rtts_fixed_set.pdf"
    plot_save(ofile, is_tight_layout=True)

def plot_accuracy_vs_number_of_vps_probes(accuracy_vs_n_vps_probes_file):

    accuracy_vs_n_vps_probes = load_json(accuracy_vs_n_vps_probes_file)
    accuracy_vs_n_vps_probes = {int(x): accuracy_vs_n_vps_probes[x] for x in accuracy_vs_n_vps_probes}
    X = sorted([x for x in sorted(accuracy_vs_n_vps_probes.keys())])
    Ys = [accuracy_vs_n_vps_probes[i] for i in X]
    Ys_med = [[np.median(x) for x in Ys]]
    Ys_err = [[np.std(x) for x in Ys]]

    """
    Fig 3.a of the paper
    """

    fig, ax = plot_multiple_error_bars(X, Ys_med, Ys_err,
                             xmin=10, xmax=10500, ymin=1, ymax=10000,
                             xlabel="Number of VPs",
                             ylabel="Geolocation error (km)",
                             xscale="log",
                             yscale="log",
                             labels=[
                                 ""
                             ],

                             )

    homogenize_legend(ax, "lower right")
    ofile = f"resources/replicability/accuracy_vs_n_vps_probes_3a.pdf"
    plot_save(ofile, is_tight_layout=True)

    """
    Fig 3.b of the paper
    """

    subset_sizes = [100, 500, 1000, 2000]

    labels = [f"{s} VPs" for s in subset_sizes]

    Ys = [accuracy_vs_n_vps_probes[i] for i in subset_sizes]
    print(min(accuracy_vs_n_vps_probes[100]), max(accuracy_vs_n_vps_probes[100]))

    fig, ax = plot_multiple_cdf(Ys, 10000, 1, 10000,
                                "Geolocation error (km)",
                                "CDF of median error",
                                xscale="log",
                                yscale="linear",
                                legend=labels)
    homogenize_legend(ax, "lower right")
    ofile = f"resources/replicability/accuracy_vs_n_vps_probes_3b.pdf"
    plot_save(ofile, is_tight_layout=True)

def plot_round_based_algorithm(round_based_algorithm_file, probes_to_anchors_results_file):

    round_based_algorithm_results = load_json(round_based_algorithm_file)

    round_based_algorithm_results = {int(x):round_based_algorithm_results[x] for x in round_based_algorithm_results}

    errors_threshold_probes_to_anchors = load_json(probes_to_anchors_results_file)
    error_threshold_cdfs_p_to_a, circles_threshold_cdfs_p_to_a, _ = compute_error_threshold_cdfs(
        errors_threshold_probes_to_anchors)

    Ys_error = [error_threshold_cdfs_p_to_a[0]]
    Ys_n_vps = []

    labels_error = ["All VPs"]
    labels_n_vps = []


    for tier1_vps, results in sorted(round_based_algorithm_results.items()):
        tier1_vps = int(tier1_vps)
        error_cdf = [r[1] for r in results if r[1] is not None]
        n_vps_cdf = [r[2] + tier1_vps for r in results if r[2] is not None]
        label = f"{tier1_vps} VPs"
        labels_error.append(label)
        labels_n_vps.append(label)
        Ys_error.append(error_cdf)
        Ys_n_vps.append(n_vps_cdf)
        print(tier1_vps, 3 * sum(n_vps_cdf))

    fig, ax = plot_multiple_cdf(Ys_error, 10000, 1, 10000,
                                "Geolocation error (km)",
                                "CDF of targets",
                                xscale="log",
                                yscale="linear",
                                legend=labels_error)
    homogenize_legend(ax, "lower right")
    ofile = f"resources/replicability/round_algorithm_error.pdf"
    plot_save(ofile, is_tight_layout=True)

    fig, ax = plot_multiple_cdf(Ys_n_vps, 10000, 10, 10000,
                                "Vantage points",
                                "CDF of representatives",
                                xscale="log",
                                yscale="linear",
                                legend=labels_n_vps)
    homogenize_legend(ax, "upper left")
    ofile = f"resources/replicability/round_algorithm_vps.pdf"
    plot_save(ofile, is_tight_layout=True)


if __name__ == "__main__":

    is_plot_error = True
    is_plot_fixed_set = False
    is_plot_accuracy_vs_number_of_vps_probes = False
    is_plot_round_based_algorithm = False

    # rtts_per_closest_probes = load_json(rtts_per_closest_probes_file)
    # plot_rtt_dist_per_target_closest_probe(rtts_per_closest_probes)
    if is_plot_error:
        results_file = [anchor_to_anchors_results_file, probes_to_anchors_results_file]
        # results_file.extend(vp_selection_algorithms_results_files)
        results_file.extend(vp_selection_algorithms_probes_results_files)
        results_file.append(fixed_set_probes_one_per_city_file)
        anchors, probes, all_probes = download_ripe_probes()
        removed_probes = load_json(removed_probes_file)
        vp_coordinates_per_ip, ip_per_coordinates, country_per_vp, asn_per_vp_ip, vp_distance_matrix, probe_per_ip = compute_geo_info(
            all_probes, serialized_file=pairwise_distance_file)

        # Compute the number of VPs per country
        vps_per_country = {}
        for vp, country in country_per_vp.items():
            if vp not in removed_probes:
                vps_per_country.setdefault(country, set()).add(vp)

        plot_error_threshold(threshold_distances, results_file, country_per_vp, vps_per_country)

    if is_plot_accuracy_vs_number_of_vps_probes:
        plot_accuracy_vs_number_of_vps_probes(accuracy_vs_n_vps_probes_file)

    if is_plot_fixed_set:
        plot_fixed_subset(fixed_set_probes_one_per_city_file, fixed_set_probes_one_per_city_asn_file, min_rtt_per_dst_file)

    if is_plot_round_based_algorithm:
        plot_round_based_algorithm(round_based_algorithm_file, probes_to_anchors_results_file)