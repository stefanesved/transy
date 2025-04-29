import os
import pandas as pd
from datetime import datetime, timedelta
from haversine import haversine, Unit

def build_gtfs(shape_file="shapes.csv", stops_file="stops.txt", output_folder="output", route_id="new_bus"):
    # ✅ Ensure output directory exists
    os.makedirs(output_folder, exist_ok=True)

    # Read stops and shape points
    stops = pd.read_csv(stops_file)
    shapes = pd.read_csv(shape_file)

    # ROUTES
    routes = pd.DataFrame([{
        "route_id": route_id,
        "agency_id": "1",
        "route_short_name": "NB1",
        "route_long_name": "New Bus Line",
        "route_type": 3  # 3 = Bus
    }])
    routes.to_csv(f"{output_folder}/routes.txt", index=False)

    # SHAPES
    shapes["shape_id"] = route_id
    shapes["shape_pt_sequence"] = range(len(shapes))
    shapes = shapes.rename(columns={"lat": "shape_pt_lat", "lon": "shape_pt_lon"})
    shapes.to_csv(f"{output_folder}/shapes.txt", index=False)

    # STOPS
    stops.to_csv(f"{output_folder}/stops.txt", index=False)

    # TRIPS
    trip_id = f"{route_id}_trip1"
    trips = pd.DataFrame([{
        "route_id": route_id,
        "service_id": "WEEKDAY",
        "trip_id": trip_id,
        "shape_id": route_id,
        "direction_id": 0
    }])
    trips.to_csv(f"{output_folder}/trips.txt", index=False)

    # STOP_TIMES
    stop_times = []
    start_time = datetime.strptime("07:00:00", "%H:%M:%S")
    for i, row in stops.iterrows():
        time = (start_time + timedelta(minutes=i)).strftime("%H:%M:%S")
        stop_times.append({
            "trip_id": trip_id,
            "arrival_time": time,
            "departure_time": time,
            "stop_id": row["stop_id"],
            "stop_sequence": i
        })
    stop_times_df = pd.DataFrame(stop_times)
    stop_times_df.to_csv(f"{output_folder}/stop_times.txt", index=False)

    # CALENDAR
    calendar = pd.DataFrame([{
        "service_id": "WEEKDAY",
        "monday": 1, "tuesday": 1, "wednesday": 1, "thursday": 1, "friday": 1,
        "saturday": 0, "sunday": 0,
        "start_date": 20250101,
        "end_date": 20251231
    }])
    calendar.to_csv(f"{output_folder}/calendar.txt", index=False)

    # LINKS (needed for Quetzal)
    links = []
    for i in range(len(stops) - 1):
        from_stop = stops.iloc[i]
        to_stop = stops.iloc[i+1]
        distance_km = haversine((from_stop["stop_lat"], from_stop["stop_lon"]),
                                (to_stop["stop_lat"], to_stop["stop_lon"]),
                                unit=Unit.KILOMETERS)
        speed_kmh = 30  # assuming bus moves at 30 km/h
        travel_time_sec = int((distance_km / speed_kmh) * 3600)

        links.append({
            "a": from_stop["stop_id"],
            "b": to_stop["stop_id"],
            "time": max(travel_time_sec, 60),  # minimum 1 minute
            "trip_id": trip_id,
            "link_sequence": i,
            "headway": 600
        })

    links_df = pd.DataFrame(links)
    links_df.to_csv(f"{output_folder}/links.txt", index=False)

    print(f"✅ GTFS files created successfully in '{output_folder}' folder.")

if __name__ == "__main__":
    build_gtfs()