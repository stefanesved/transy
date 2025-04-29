import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, Point
import numpy as np

def generate_stops_from_csv(csv_path="new_route.csv", output_path="stops.txt", spacing=400):
    df = pd.read_csv(csv_path)
    line = LineString([Point(xy) for xy in zip(df["lon"], df["lat"])])
    length = line.length

    # Generate points at regular intervals
    num_points = int(length // (spacing / 1e5))  # Adjust for lon/lat approx scale
    distances = np.linspace(0, 1, num_points)

    stops = []
    for i, d in enumerate(distances):
        point = line.interpolate(d, normalized=True)
        stops.append({"stop_id": f"stop_{i}", "stop_name": f"Stop {i}", 
                      "stop_lat": point.y, "stop_lon": point.x})

    stops_df = pd.DataFrame(stops)
    stops_df.to_csv(output_path, index=False)
    print(f"✅ Generated {len(stops)} stops → {output_path}")

if __name__ == "__main__":
    generate_stops_from_csv()
