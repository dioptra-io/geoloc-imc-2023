import rasterio
import geopandas as gpd
from rasterio.transform import from_bounds
import json


if __name__ == "__main__":
    resources_dir = "resources/replicability/street/"
    # Load the population density data
    with rasterio.open(f'{resources_dir}/gpw_v4_population_density_rev11_2020_30_sec.tif') as dataset:
        population_density = dataset.read(1)


    ofile = f"{resources_dir}/population_target.json"

    with open(ofile) as f:
        all_data = json.load(f)

    res = []
    for d in all_data:
        if 'density' not in d:
            lat, lon = d['lat'], d['lon']
            point = gpd.GeoDataFrame(geometry=gpd.points_from_xy([lon], [lat]))

            # Convert lat-lon to pixel coordinates
            xmin, ymin, xmax, ymax = dataset.bounds
            transform = from_bounds(xmin, ymin, xmax, ymax, dataset.width, dataset.height)
            row, col = dataset.index(lon, lat)

            # Extract the population density value
            population_density_value = population_density[row, col]
            d['density'] = float(population_density_value)

        res.append(d)
    with open(ofile, "w") as f:
        json.dump(res, f)