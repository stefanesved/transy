import dash
import dash_leaflet as dl
import dash_bootstrap_components as dbc
from dash import dcc, html, Output, Input, State, ctx, no_update
import geopandas as gpd
import pandas as pd
import json
import os

# Initialize app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Transy - Transport Line Builder"
server = app.server

# Status tracker
status_store = {
    'gtfs_created': False,
    'model_built': False,
    'accessibility_done': False
}

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("Transy 🚍", className="text-center mb-4"),
            dbc.Button("Generate GTFS", id="generate-gtfs-btn", color="primary", className="mb-2", style={'width': '100%'}),
            dbc.Button("Run Model", id="run-model-btn", color="success", className="mb-4", style={'width': '100%'}),
            dcc.Loading(
                id="loading-model",
                type="circle",
                children=dbc.Card([
                    dbc.CardHeader("Progress Tracker"),
                    dbc.CardBody([
                        html.Ul([
                            html.Li(id="gtfs-status", children="❌ GTFS not generated"),
                            html.Li(id="model-status", children="❌ Model not built"),
                            html.Li(id="accessibility-status", children="❌ Accessibility not computed"),
                        ])
                    ])
                ])
            )
        ], width=3, style={"background-color": "#f8f9fa", "padding": "20px"}),

        dbc.Col([
            dl.Map(
                id="map",
                center=[45.5017, -73.5673],
                zoom=12,
                style={'width': '100%', 'height': '90vh', 'cursor': 'crosshair'},
                children=[
                    dl.TileLayer(),
                    dl.FeatureGroup([
                        dl.EditControl(
                            id="edit-control",
                            draw={'polyline': True, 'marker': True, 'polygon': False, 'rectangle': False, 'circlemarker': False, 'circle': False},
                            edit={'edit': False, 'remove': True},
                            position="topleft",
                        )
                    ]),
                    dl.LayerGroup(id="layer-polylines"),
                ]
            ),
            html.Div(id="map-info", className="mt-3")
        ], width=9)
    ])
], fluid=True)

# --- Callbacks

@app.callback(
    [Output("map-info", "children"),
     Output("layer-polylines", "children"),
     Output("gtfs-status", "children"),
     Output("gtfs-status", "style")],
    [Input("edit-control", "geojson"),
     Input("generate-gtfs-btn", "n_clicks")],
    [State("edit-control", "geojson")]
)
def generate_gtfs(geojson, n_clicks, current_geojson):
    trigger_id = ctx.triggered_id

    if trigger_id == "generate-gtfs-btn" and current_geojson:
        coords = current_geojson["features"][0]["geometry"]["coordinates"]

        if len(coords) < 2:
            return "⚠️ Draw at least two points!", [], no_update, no_update

        stops = []
        links = []
        stop_times = []

        for i, (lon, lat) in enumerate(coords):
            stops.append({
                "stop_id": f"stop_{i}",
                "stop_name": f"Stop {i}",
                "stop_lat": lat,
                "stop_lon": lon
            })

            stop_times.append({
                "trip_id": "new_bus_trip1",
                "arrival_time": f"07:{str(i).zfill(2)}:00",
                "departure_time": f"07:{str(i).zfill(2)}:00",
                "stop_id": f"stop_{i}",
                "stop_sequence": i
            })

        for i in range(1, len(stops)):
            links.append({
                "a": stops[i-1]['stop_id'],
                "b": stops[i]['stop_id'],
                "time": 60,
                "trip_id": "new_bus_trip1",
                "link_sequence": i-1,
                "headway": 600
            })

        trips = [{
            "route_id": "new_bus_route1",
            "service_id": "weekday",
            "trip_id": "new_bus_trip1",
            "direction_id": 0  # ✅ FIXED
        }]

        routes = [{
            "route_id": "new_bus_route1",
            "agency_id": "agency1",
            "route_short_name": "NB1",
            "route_long_name": "New Bus Route 1",
            "route_type": 3  # 3 = Bus
        }]

        os.makedirs("output", exist_ok=True)

        pd.DataFrame(stops).to_csv("output/stops.txt", index=False)
        pd.DataFrame(links).to_csv("output/links.txt", index=False)
        pd.DataFrame(stop_times).to_csv("output/stop_times.txt", index=False)
        pd.DataFrame(trips).to_csv("output/trips.txt", index=False)
        pd.DataFrame(routes).to_csv("output/routes.txt", index=False)

        status_store['gtfs_created'] = True

        points = [(lat, lon) for lon, lat in coords]
        markers = [dl.CircleMarker(center=pt, radius=6, color='red', fillColor='red', fillOpacity=1) for pt in points]
        polyline = dl.Polyline(positions=points, color="red", weight=6)

        return "✅ GTFS created with {} stops".format(len(stops)), markers + [polyline], "✅ GTFS generated", {"color": "green"}

    if current_geojson and "features" in current_geojson and len(current_geojson["features"]) > 0:
        coords = current_geojson["features"][0]["geometry"]["coordinates"]
        points = [(lat, lon) for lon, lat in coords]
        markers = [dl.CircleMarker(center=pt, radius=6, color='red', fillColor='red', fillOpacity=1) for pt in points]
        polyline = dl.Polyline(positions=points, color="red", weight=6)
        return f"✍️ {len(points)} points selected", markers + [polyline], no_update, no_update

    return no_update, no_update, no_update, no_update

@app.callback(
    [Output("model-status", "children"),
     Output("model-status", "style"),
     Output("accessibility-status", "children"),
     Output("accessibility-status", "style")],
    Input("run-model-btn", "n_clicks")
)
def run_model(n_clicks):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    try:
        os.system("python model/quetzal_model.py")
        status_store['model_built'] = True
        status_store['accessibility_done'] = True
        return ("✅ Model built", {"color": "green"}, "✅ Accessibility computed", {"color": "green"})
    except Exception as e:
        return ("❌ Model error", {"color": "red"}, "❌ Accessibility error", {"color": "red"})

if __name__ == "__main__":
    # app.run(debug=True)
    import os
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=True)