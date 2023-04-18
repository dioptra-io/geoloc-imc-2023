import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from math import cos, sin, pi
from utils.helpers import rtt_to_km

def draw_results(probe_circles, intersections, target):

    test_circles = {}
    for key, (lat, lon, rtt, _, _) in probe_circles.items():
        d = rtt_to_km(rtt,  4/9)
        #print(f"circle to draw: {key} : {lat, lon, d}")
        test_circles[key] = (lat, lon, d)

    df_circles = pd.DataFrame({
        'Latitude': np.array([lat_long[0] for lat_long in test_circles.values()]),
        'Longitude': np.array([lat_long[1] for lat_long in test_circles.values()]),
        'Radius': np.array([lat_long[2] for lat_long in test_circles.values()]),
    })

    fig_map3 = px.scatter_mapbox(df_circles['Radius'], lon=df_circles['Longitude'], lat=df_circles['Latitude'],
                                hover_name='Radius', zoom=9, width=300, height=500)

    N = 360
    for i, (index, row) in enumerate(df_circles.iterrows()):
        circle_lats, circle_lons = [], []

        lat = df_circles['Latitude'][i]
        lon = df_circles['Longitude'][i]
        r = df_circles['Radius'][i]

        for k in range(N):
            # compute
            angle = pi*2*k/N
            dx = r*1000*cos(angle)
            dy = r*1000*sin(angle)
            circle_lats.append(lat + (180/pi)*(dy/6378137))
            circle_lons.append(lon + (180/pi)*(dx/6378137)/cos(lat*pi/180))

        circle_lats.append(circle_lats[0])
        circle_lons.append(circle_lons[0])

        fig_map3.add_trace(go.Scattermapbox(
            lat=circle_lats,
            lon=circle_lons,
            mode='lines',
            marker=go.scattermapbox.Marker(
                size=1, color="BlueViolet"
            ),
        ))

    # add calculated intersections
    print("calculated intersections:")
    for lat, lon in intersections:
        print(lat, lon)
        fig_map3.add_trace(go.Scattermapbox(
            lat=[lat],
            lon=[lon],
            marker=go.scattermapbox.Marker(
                size=10, color="Red"
            ),
        ))

    print("target:")
    fig_map3.add_trace(go.Scattermapbox(
        lat=[target[0]],
        lon=[target[1]],
        marker=go.scattermapbox.Marker(
            size=10, color="Green"
        ),
    ))
    print(lat, lon)

    fig_map3.update_layout(mapbox_style='open-street-map', margin={'r':0, 't':0, 'l':0, 'b':0}, width=500)
    fig_map3.show()