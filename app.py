from dash import Dash, html, Output, Input, State, dcc, ctx
import dash_leaflet as dl
import dash_bootstrap_components as dbc
import json
import pandas as pd

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H1("New Bus Line Designer"),
    dl.Map(
        center=[19.4326, -99.1332],
        zoom=13,
        children=[
            dl.TileLayer(),
            dl.FeatureGroup([
                dl.EditControl(
                    id="edit-control",
                    draw={"polyline": True, "polygon": False, "marker": False},
                    edit={"edit": True}
                )
            ])
        ],
        id="map",
        style={'width': '100%', 'height': '80vh'},
    ),
    dcc.Store(id="geometry-store"),
    dbc.Button("💾 Save Route", id="save-btn", color="primary", className="mt-3"),
    html.Div(id="output", className="mt-2")
], fluid=True)

# Store the geometry when drawn
@app.callback(
    Output("geometry-store", "data"),
    Input("edit-control", "geojson"),
)
def store_drawn_route(geojson):
    return geojson

# Save to file on button click
@app.callback(
    Output("output", "children"),
    Input("save-btn", "n_clicks"),
    State("geometry-store", "data"),
    prevent_initial_call=True
)
def save_route(n_clicks, geojson):
    if not geojson:
        return "No route to save."

    features = geojson.get("features", [])
    coords = []
    for feature in features:
        if feature["geometry"]["type"] == "LineString":
            coords.extend(feature["geometry"]["coordinates"])

    # Save as CSV
    df = pd.DataFrame(coords, columns=["lon", "lat"])
    df.to_csv("new_route.csv", index=False)

    # Optional: also save GeoJSON
    with open("new_route.geojson", "w") as f:
        json.dump(geojson, f, indent=2)

    return f"✅ Route saved as new_route.csv and new_route.geojson"

if __name__ == "__main__":
    app.run(debug=True)