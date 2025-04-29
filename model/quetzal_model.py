import geopandas as gpd
import pandas as pd
import os
from shapely.geometry import Point
from quetzal.model.stepmodel import StepModel
from quetzal.io.gtfs_reader.gtfs_importer import BaseGtfsImporter
from quetzal.engine.pathfinder_utils import link_edge_array, paths_from_edges


def custom_accessibility(model, threshold=1800):
    if not hasattr(model, 'paths') or model.paths.empty:
        print("\u26a0\ufe0f No paths data found for accessibility computation.")
        return pd.DataFrame()

    reachable = model.paths[model.paths['length'] <= threshold]
    accessibility = reachable.groupby('origin').size().reset_index(name='accessible_destinations')
    return accessibility


def run_model(gtfs_folder="output", output_path="output/accessibility_results.csv"):
    print("\n[GTFS] Reading GTFS with BaseGtfsImporter...")
    importer = BaseGtfsImporter(gtfs_folder + '/')
    importer.read()
    importer.build()

    model = StepModel()
    model.results = {}
    model.links = importer.links
    model.nodes = importer.stops

    model.links['headway'] = 600
    model.nodes.index = [f"node_{i}" for i in range(len(model.nodes))]
    model.links.index = [f"link_{i}" for i in range(len(model.links))]

    model.zones = gpd.GeoDataFrame(
        importer.stops.copy(),
        geometry=[Point(xy) for xy in zip(importer.stops['stop_lon'], importer.stops['stop_lat'])],
        crs="EPSG:4326"
    )
    model.zones.index = [f"zone_{i}" for i in range(len(model.zones))]

    model.footpaths = pd.DataFrame(columns=['a', 'b', 'time'])
    model.zone_to_transit = pd.DataFrame({
        'a': model.zones.index,
        'b': model.nodes.index[:len(model.zones)],
        'time': 0
    })

    print("\n[Model] Running step_pathfinder...")
    try:
        model.step_pathfinder()
    except Exception as e:
        print(f"\u26a0\ufe0f Step pathfinder error: {e}")

    print("\n\ud83d\udcca Model structure summary:")
    print("\u2705 Links:", model.links.shape)
    print("\u2705 Nodes:", model.nodes.shape)
    print("\u2705 Zones:", model.zones.shape)
    print("\u2705 Footpaths:", model.footpaths.shape)
    print("\u2705 Zone to Transit:", model.zone_to_transit.shape)

    print("\n\ud83d\udcc8 Running accessibility analysis...")
    try:
        print("\uD83D\uDD0D Computing accessibility within threshold...")
        edges = link_edge_array(model.links, boarding_time=0, alighting_time=0).tolist()
        model.paths = paths_from_edges(
            edges=edges,
            sources=model.nodes.index.tolist(),
            targets=model.nodes.index.tolist(),
            od_set={(o, d) for o in model.nodes.index for d in model.nodes.index if o != d},
            cutoff=1800,
            penalty=1e9,
            log=True
        )
        acc = custom_accessibility(model, threshold=1800)
        model.results['accessibility'] = acc
    except Exception as e:
        print(f"\u26a0\ufe0f Accessibility analysis failed: {e}")
        model.results['accessibility'] = pd.DataFrame()

    acc = model.results.get('accessibility')
    if acc is not None and not acc.empty:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        acc.to_csv(output_path, index=False)
        print(f"\u2705 Accessibility results saved to {output_path}")
    else:
        print("\u26a0\ufe0f Accessibility results are empty or unavailable.")


if __name__ == "__main__":
    run_model()