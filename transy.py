import dash
import dash_leaflet as dl
import dash_bootstrap_components as dbc
from dash import dcc, html, Output, Input, State, ctx, no_update
import geopandas as gpd
import pandas as pd
import os

# Initialize app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

status_store = {
    'gtfs_created': False,
    'model_built': False,
    'accessibility_done': False
}

app.layout = dbc.Container([
    dbc.Row([
        # Sidebar
        dbc.Col([
            html.H2("Transy 🚍", className="text-center mb-4"),
            dbc.Button("Generate GTFS", id="generate-gtfs-btn", color="primary", className="mb-2", style={"width": "100%"}),
            dbc.Button("Run Model", id="run-model-btn", color="success", className="mb-4", style={"width": "100%"}),
            dbc.Card([
                dbc.CardHeader("Progress Tracker"),
                dbc.CardBody([
                    html.Ul([
                        html.Li(id="gtfs-status", children="❌ GTFS not generated"),
                        html.Li(id="model-status", children="❌ Model not built"),
                        html.Li(id="accessibility-status", children="❌ Accessibility not computed"),
                    ])
                ])
            ]),
        ], width=3, style={"background-color": "#f8f9fa", "padding": "20px"}),

        # Main Map
        dbc.Col([
            dl.Map(
                id="map",
                center=[45.5017, -73.5673],
                zoom=13,
                style={'width': '100%', 'height': '90vh', 'cursor': 'grab'},
                children=[
                    dl.TileLayer(),
                    dl.FeatureGroup([
                        dl.EditControl(
                            id="edit-control",
                            position="topleft",
                            draw=dict(
                                polyline=True,
                                polygon=False,
                                rectangle=False,
                                circlemarker=False,
                                marker=True,
                                circle=False,
                            ),
                            edit=dict(
                                edit=False,
                                remove=True,
                            ),
                        )
                    ]),
                    dl.LayerGroup(id="layer-polylines"),
                ]
            ),
            html.Div(id="map-info", className="mt-3")
        ], width=9)
    ])
], fluid=True)

# Callbacks
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

        stops = []
        links = []
        for i, (lon, lat) in enumerate(coords):
            stops.append({
                "stop_id": f"stop_{i}",
                "stop_name": f"Stop {i}",
                "stop_lat": lat,
                "stop_lon": lon
            })
            if i > 0:
                links.append({
                    "a": f"stop_{i-1}",
                    "b": f"stop_{i}",
                    "time": 60,
                    "trip_id": "new_bus_trip1",
                    "link_sequence": i-1,
                    "headway": 600
                })

        os.makedirs("output", exist_ok=True)
        pd.DataFrame(stops).to_csv("output/stops.txt", index=False)
        pd.DataFrame(links).to_csv("output/links.txt", index=False)

        status_store['gtfs_created'] = True
        return "✅ GTFS created with {} stops".format(len(stops)), [], "✅ GTFS generated", {"color": "green"}

    if current_geojson:
        points = [(lat, lon) for lon, lat in current_geojson["features"][0]["geometry"]["coordinates"]]
        markers = [
            dl.CircleMarker(center=pt, radius=6, color='red', fillColor='red', fillOpacity=1) for pt in points
        ]
        polyline = dl.Polyline(positions=points, color="red", weight=5)
        return f"✏️ {len(points)} points selected", markers + [polyline], no_update, no_update

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
    app.run(debug=True)