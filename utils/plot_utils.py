import matplotlib.pyplot as plt
import matplotlib
import plotly.express as px
import pandas as pd

from matplotlib.patches import Polygon
from matplotlib.lines import Line2D

from utils.helpers import circle_preprocessing, get_points_on_circle


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


def plot_dots_from_df(df):
    df.dropna(
        axis=0,
        how='any',
        subset=None,
        inplace=True
    )
    color_scale = [(0, 'orange'), (1, 'red')]
    fig = px.scatter_mapbox(df,
                            lat="lat",
                            lon="lon",
                            color="color",
                            color_continuous_scale=color_scale,
                            zoom=8,
                            height=800,
                            width=800)

    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.show()


def circle_df_around_point(lat, lon, rad):
    edges = get_points_on_circle(lat, lon, rad, 360)
    lons = [lon]
    lats = [lat]
    colores = [1]
    for e in edges:
        lats.append(e[0])
        lons.append(e[1])
        colores.append(0)
    df = pd.DataFrame(list(zip(lons, lats, colores)),
                      columns=['lon', 'lat', 'color'])
    return df


def plot_circles_and_points(circles, points, speed_threshold=4/9):
    circles = circle_preprocessing(circles, speed_threshold=speed_threshold)
    frames = []
    for circle in circles:
        frames.append(circle_df_around_point(circle[0], circle[1], circle[3]))

    lons = []
    lats = []
    colores = []
    for p in points:
        lats.append(p[0])
        lons.append(p[1])
        colores.append(0.5)

    frames.append(pd.DataFrame(list(zip(lons, lats, colores)),
                               columns=['lon', 'lat', 'color']))

    df = pd.concat(frames, ignore_index=True)
    plot_dots_from_df(df)
