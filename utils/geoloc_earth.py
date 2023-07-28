import pandas as pd
import plotly.express as px

from utils.helpers import circle_preprocessing, circle_intersections, polygon_centroid, is_within_cirle, get_points_on_circle


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


def get_center_of_poly(circles, speed):
    points = circle_intersections(circles, speed)
    if len(points) == 0:
        return None, None
    return polygon_centroid(points)


def get_points_in_poly(circles, rot, rad, speed, old_circles=[]):
    circles = circle_preprocessing(circles, speed_threshold=speed)
    points = circle_intersections(circles, speed)
    if len(points) == 0:
        return []
    else:
        center = polygon_centroid(points)
    res = [center]
    iter_rad = 0
    points_added = True
    while points_added:
        iter_rad += rad
        points_added = False
        to_add_points = get_points_on_circle(
            center[0], center[1], iter_rad, int(360/rot))
        for point in to_add_points:
            all_in = True
            for vp in circles:
                if not is_within_cirle((vp[0], vp[1]), vp[2], point, speed):
                    all_in = False
                    break
            if all_in:
                for vp in old_circles:
                    if not is_within_cirle((vp[0], vp[1]), vp[2], point, speed):
                        all_in = False
                    break
                if all_in:
                    points_added = True
                    res.append(point)
    return res
