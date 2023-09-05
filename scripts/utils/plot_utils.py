# Functions to plot figures in a nice way

import matplotlib.pyplot as plt
import matplotlib

from matplotlib.patches import Polygon
from matplotlib.lines import Line2D


matplotlib.use('Agg')

font = {  # 'family' : 'normal',
    'weight': 'bold',
    'size': 16
}
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
fontsize_axis = 17
font_size_alone = 14
matplotlib.rc('font', **font)

markers = ["o", "s", "v", "^"]
linestyles = ["-", "--", "-.", ":"]

colors_blind = [
    ["blue", (0, 114.0/255, 178.0/255)],
    ["orange", (230.0/255, 159.0/255, 0)],
    ["reddish_purple", (204.0 / 255, 121.0 / 255, 167.0 / 255)],
    ["black", (0, 0, 0)],
    ["bluish_green", (0, 158.0/255, 115.0/255)],
    ["sky_blue", (86.0/255, 180.0/255, 233.0/255)],
    ["vermillon", (213.0/255, 94.0/255, 0)],
    # ["yellow", (240.0 / 255, 228.0 / 255, 66.0 / 255)],
]


def plot_multiple_cdf(Ys, n_bins,
                      xmin, xmax,
                      xlabel, ylabel,
                      legend,
                      ymin=0,
                      ymax=1.05,
                      xticks=None,
                      xticks_labels=None,
                      xscale="linear", yscale="linear",
                      cumulative=True,
                      figure=None, axes=None,
                      offset=0,
                      colors_arg=None,
                      linestyles_arg=None):

    if figure is not None and axes is not None:
        fig = figure
        ax = axes
    else:
        subplots = plt.subplots()
        fig, ax = subplots
    ax.set_xlabel(xlabel, fontsize=fontsize_axis)
    ax.set_ylabel(ylabel, fontsize=fontsize_axis)
    # title = title + " CDF"
    # plt.title("CDF", fontsize=fontsize_axis)

    ax.grid(linestyle="dotted")
    if len(Ys) == 1:
        i = 0
        Y = Ys[i]
        if colors_arg is not None:
            color = colors_arg[i][1]
        else:
            color = colors_blind[(i + offset) % len(colors_blind)][1]

        if linestyles_arg is not None:
            linestyle = linestyles[i]
        else:
            linestyle = linestyles[(i + offset) % len(linestyles)]

        n, bins, patches = ax.hist(Y, density=True, histtype='step', bins=n_bins,
                                   cumulative=cumulative, linewidth=1.35,
                                   color=color,
                                   linestyle=linestyle)
        patches[0].set_xy(patches[0].get_xy()[1:-1])
    else:
        for i in range(0, len(Ys)):
            Y = Ys[i]
            if colors_arg is not None:
                color = colors_arg[i][1]
            else:
                color = colors_blind[(i + offset) % len(colors_blind)][1]

            if linestyles_arg is not None:
                linestyle = linestyles_arg[i]
            else:
                linestyle = linestyles[(i + offset) % len(linestyles)]

            n, bins, patches = ax.hist(Y, density=True, histtype='step', bins=n_bins,
                                       cumulative=cumulative, linewidth=1.35, label=legend[i],
                                       color=color,
                                       linestyle=linestyle)
            patches[0].set_xy(patches[0].get_xy()[1:-1])

    # plt.xscale("symlog")
    # xticks = ax.xaxis.get_major_ticks()
    # xticks[1].label1.set_visible(False)
    # # xticks[2].label1.set_visible(False)
    # xticks[-2].label1.set_visible(False)
    ax.set_xscale(xscale)
    ax.set_yscale(yscale)
    ax.set_xlim(left=xmin, right=xmax)
    ax.set_ylim(bottom=ymin, top=ymax)
    if xticks is not None:
        ax.set_xticks(xticks)
    # xtickNames = plt.setp(ax, xticklabels=[f"{r}" for r in x_ticks])
    if xticks_labels is not None:
        ax.set_xticklabels(xticks_labels)

    # Normalize the data to a proper PDF
    # plt.tight_layout()
    # plt.savefig(r"resources/figures/" + ofile + ".pdf")
    return fig, ax


def plot_multiple_error_bars(X, Ys, Yerrs,
                             xmin, xmax, ymin, ymax,
                             xlabel, ylabel,
                             xscale, yscale,
                             labels):
    fig, ax = plt.subplots()
    ax.set_xlabel(xlabel, fontsize=fontsize_axis)

    ax.set_ylabel(ylabel, fontsize=fontsize_axis)
    ax.grid(linestyle="dotted")

    # x_ticks = [inf_born+1]
    for i in range(len(Ys)):

        Y = Ys[i]
        Yerr = Yerrs[i]
        lns1 = ax.errorbar(X, Y, Yerr,  label=labels[i], linewidth=0.5,
                           marker=markers[i % len(markers)], markersize=1, markeredgewidth=1,
                           capsize=2)
    ax.set_xscale(xscale)
    ax.set_yscale(yscale)
    ax.set_xlim(left=xmin, right=xmax)
    ax.set_ylim(bottom=ymin, top=ymax)
    return fig, ax


def plot_save(ofile, is_tight_layout):
    if is_tight_layout:
        plt.tight_layout()
    # plt.show()
    plt.savefig(ofile)

    # plt.clf()


def homogenize_legend(ax, legend_location, legend_size=14):
    handles, labels = ax.get_legend_handles_labels()
    new_handles = []
    for h in handles:
        if isinstance(h, Line2D):
            new_handles.append(h)
        elif isinstance(h, Polygon):
            new_handles.append(
                Line2D([], [], linestyle=h.get_linestyle(), color=h.get_edgecolor()))
    ax.legend(loc=legend_location, prop={
              "size": legend_size}, handles=new_handles, labels=labels)


def plot_scatter_multiple(Xs, Ys, xmin, xmax, ymin, ymax, xscale, yscale, xlabel, ylabel,
                          markers, marker_colors, marker_size):
    fig, ax = plt.subplots()

    # ax.set_xlabel(title, fontsize=fontsize_axis)
    # plt.title("CDF", fontsize=fontsize_axis)

    # x_ticks = [inf_born]
    # x_ticks.extend(np.arange(inf_born, sup_born, xtick_interval))
    # ax.set_xticks(x_ticks)
    # xtickNames = plt.setp(ax, xticklabels=["{0:.1f}".format(r) for r in x_ticks])
    # ax.set_xticklabels(xtickNames, rotation=45)
    # ax.set_xticklabels(xtickNames)

    ax.grid(linestyle="dotted")
    ax.set_xlabel(xlabel, fontsize=fontsize_axis)
    ax.set_ylabel(ylabel, fontsize=fontsize_axis)

    for i in range(0, len(Xs)):
        X = Xs[i]
        Y = Ys[i]

        # , markersize=10, markeredgewidth=2)
        ax.scatter(X, Y, c=marker_colors[i],
                   marker=markers[i], s=marker_size[i])
        # ax.plot(X, Y)
        # patches[0].set_xy(patches[0].get_xy()[:-1])
    ax.set_xscale(xscale)
    ax.set_yscale(yscale)

    ax.set_xlim(left=xmin, right=xmax)
    ax.set_ylim(bottom=ymin, top=ymax)

    return fig, ax
