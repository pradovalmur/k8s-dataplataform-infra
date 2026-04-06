import logging

import pandas as pd
from dash import Dash, dcc, html, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objects as go
from flask import jsonify

from services.trino_queries import load_satellites, load_filter_values

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Dash(__name__)
server = app.server

APP_TITLE = "Orbital Tracking Dashboard"

QUICK_TARGETS = {
    "ISS": ["ISS", "ZARYA"],
    "Tiangong": ["TIANHE", "WENTIAN", "MENGTIAN", "TIANGONG"],
    "Hubble": ["HST", "HUBBLE"],
    "Starlink": ["STARLINK"],
    "GPS": ["NAVSTAR"],
    "Galileo": ["GALILEO"],
}

STARLINK_GROUP_OPTIONS = [
    {"label": "All", "value": "All"},
    {"label": "53° shell", "value": "Starlink 53°"},
    {"label": "43° shell", "value": "Starlink 43°"},
    {"label": "70° shell", "value": "Starlink 70°"},
    {"label": "Polar shell", "value": "Starlink Polar"},
    {"label": "Other", "value": "Starlink Other"},
]


@server.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


def build_options(values):
    return [{"label": v, "value": v} for v in values if v is not None]


def get_filters():
    try:
        filters = load_filter_values()
        logger.info(
            "Loaded filters: owner=%s object_type=%s",
            len(filters.get("owner", [])),
            len(filters.get("object_type", [])),
        )
        return filters
    except Exception:
        logger.exception("Failed to load filters from Trino")
        return {
            "owner": [],
            "object_type": [],
        }


filters = get_filters()

app.layout = html.Div(
    className="app-shell",
    children=[
        dcc.Store(id="satellite-data"),
        dcc.Interval(id="auto-refresh", interval=300 * 1000, n_intervals=0),
        html.Div(
            className="content full-width",
            children=[
                html.Div(
                    className="topbar",
                    children=[
                        html.Div(
                            children=[
                                html.Div("SPACE", className="brand-tag"),
                                html.H1(APP_TITLE, className="page-title"),
                                html.P(
                                    "Current satellite positions and metadata",
                                    className="page-subtitle",
                                ),
                            ]
                        ),
                        html.Div(
                            className="topbar-actions",
                            children=[
                                html.Button(
                                    "Filters",
                                    id="toggle-filters-btn",
                                    n_clicks=0,
                                    className="action-btn secondary-btn",
                                ),
                                html.Button(
                                    "Refresh data",
                                    id="refresh-btn",
                                    n_clicks=0,
                                    className="action-btn primary-btn",
                                ),
                            ],
                        ),
                        html.Div(id="kpi-cards", className="kpi-row"),
                    ],
                ),
                html.Div(
                    id="filters-wrapper",
                    className="filters-drawer",
                    children=[
                        html.Div(
                            className="filter-panel",
                            children=[
                                html.H4("Filters", className="section-title"),
                                html.Div(
                                    className="filter-grid filter-grid-3",
                                    children=[
                                        html.Div(
                                            className="filter-block",
                                            children=[
                                                html.Label("Owner"),
                                                dcc.Dropdown(
                                                    id="owner-filter",
                                                    options=build_options(filters.get("owner", [])),
                                                    multi=True,
                                                    placeholder="All owners",
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            className="filter-block",
                                            children=[
                                                html.Label("Object type"),
                                                dcc.Dropdown(
                                                    id="object-type-filter",
                                                    options=build_options(filters.get("object_type", [])),
                                                    multi=True,
                                                    placeholder="All object types",
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            className="filter-block",
                                            children=[
                                                html.Label("Quick target"),
                                                dcc.Dropdown(
                                                    id="quick-target-filter",
                                                    options=build_options(list(QUICK_TARGETS.keys())),
                                                    multi=False,
                                                    placeholder="Select a target",
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                html.Div(
                                    id="starlink-subfilter-wrapper",
                                    style={"display": "none", "marginTop": "16px"},
                                    children=[
                                        html.Div(
                                            className="filter-block",
                                            children=[
                                                html.Label("Starlink group"),
                                                dcc.Dropdown(
                                                    id="starlink-group-filter",
                                                    options=STARLINK_GROUP_OPTIONS,
                                                    value="All",
                                                    clearable=False,
                                                ),
                                            ],
                                        )
                                    ],
                                ),
                            ],
                        )
                    ],
                ),
                html.Div(
                    className="map-card full-map-card",
                    children=[
                        html.Div(
                            className="card-header",
                            children=[html.H3("Global map")],
                        ),
                        dcc.Graph(
                            id="satellite-map",
                            style={"height": "78vh"},
                            config={
                                "scrollZoom": False,
                                "displayModeBar": True,
                            },
                        ),
                    ],
                ),
                html.Div(
                    className="details-card full-details-card",
                    children=[
                        html.Div(
                            className="card-header",
                            children=[html.H3("Satellite details")],
                        ),
                        html.Div(id="selected-satellite", className="selected-panel"),
                        html.Div(
                            className="card-header secondary",
                            children=[html.H3("Visible rows")],
                        ),
                        dash_table.DataTable(
                            id="satellite-table",
                            page_size=12,
                            sort_action="native",
                            style_table={"overflowX": "auto"},
                            style_cell={
                                "backgroundColor": "#f8fafc",
                                "color": "#0f172a",
                                "border": "1px solid #dbe4f0",
                                "fontSize": "12px",
                                "padding": "8px",
                                "textAlign": "left",
                            },
                            style_header={
                                "backgroundColor": "#e2e8f0",
                                "color": "#0f172a",
                                "fontWeight": "bold",
                                "border": "1px solid #cbd5e1",
                            },
                        ),
                    ],
                ),
            ],
        ),
    ],
)


@app.callback(
    Output("filters-wrapper", "style"),
    Input("toggle-filters-btn", "n_clicks"),
)
def toggle_filters(n_clicks):
    if n_clicks and n_clicks % 2 == 1:
        return {"display": "none"}
    return {"display": "block"}


@app.callback(
    Output("starlink-subfilter-wrapper", "style"),
    Input("quick-target-filter", "value"),
)
def toggle_starlink_subfilter(quick_target):
    if quick_target == "Starlink":
        return {"display": "block", "marginTop": "16px"}
    return {"display": "none"}


@app.callback(
    Output("satellite-data", "data"),
    Input("refresh-btn", "n_clicks"),
    Input("auto-refresh", "n_intervals"),
)
def refresh_data(_n_clicks, _n_intervals):
    try:
        df = load_satellites()
        logger.info("Loaded %s satellites for dashboard", len(df))
        return df.to_dict("records")
    except Exception:
        logger.exception("Failed to load satellite data from Trino")
        return []


@app.callback(
    Output("satellite-map", "figure"),
    Output("satellite-table", "data"),
    Output("satellite-table", "columns"),
    Output("kpi-cards", "children"),
    Input("satellite-data", "data"),
    Input("owner-filter", "value"),
    Input("object-type-filter", "value"),
    Input("quick-target-filter", "value"),
    Input("starlink-group-filter", "value"),
)
def update_dashboard(data, owners, object_types, quick_target, starlink_group):
    df = pd.DataFrame(data or [])

    if df.empty:
        fig = px.scatter_mapbox(lat=[], lon=[], zoom=1)
        fig.update_layout(
            mapbox=dict(
                style="carto-positron",
                center={"lat": 15, "lon": 0},
                zoom=1,
                bounds={
                    "west": -180,
                    "east": 180,
                    "south": -75,
                    "north": 85,
                },
            ),
            margin={"l": 0, "r": 0, "t": 0, "b": 0},
            paper_bgcolor="#eef4fb",
        )
        empty_message = [
            html.Div(
                className="kpi-card",
                children=[html.Span("Status"), html.H3("No data loaded")],
            )
        ]
        return fig, [], [], empty_message

    if owners and "owner" in df.columns:
        df = df[df["owner"].isin(owners)]

    if object_types and "object_type" in df.columns:
        df = df[df["object_type"].isin(object_types)]

    if quick_target and "object_name" in df.columns:
        terms = [t.upper() for t in QUICK_TARGETS.get(quick_target, [])]
        if terms:
            mask = pd.Series(False, index=df.index)
            names = df["object_name"].fillna("").astype(str).str.upper()
            for term in terms:
                mask = mask | names.str.contains(term, regex=False)
            df = df[mask]

    if quick_target == "Starlink" and starlink_group and starlink_group != "All":
        if "starlink_group" in df.columns:
            df = df[df["starlink_group"] == starlink_group]

    if df.empty:
        fig = px.scatter_mapbox(lat=[], lon=[], zoom=1)
        fig.update_layout(
            mapbox=dict(
                style="carto-positron",
                center={"lat": 15, "lon": 0},
                zoom=1,
                bounds={
                    "west": -180,
                    "east": 180,
                    "south": -75,
                    "north": 85,
                },
            ),
            margin={"l": 0, "r": 0, "t": 0, "b": 0},
            paper_bgcolor="#eef4fb",
        )
        empty_message = [
            html.Div(
                className="kpi-card",
                children=[html.Span("Status"), html.H3("No rows after filters")],
            )
        ]
        return fig, [], [], empty_message

    color_col = None
    if "object_type" in df.columns and df["object_type"].notna().any():
        color_col = "object_type"

    custom_cols = []
    for col in ["norad_id", "altitude_km", "velocity_km_s", "owner", "object_type"]:
        if col in df.columns:
            custom_cols.append(col)
    if "starlink_group" in df.columns:
        custom_cols.append("starlink_group")

    hover_data = {
        "latitude": False,
        "longitude": False,
    }
    if "norad_id" in df.columns:
        hover_data["norad_id"] = True
    if "altitude_km" in df.columns:
        hover_data["altitude_km"] = ":.2f"
    if "velocity_km_s" in df.columns:
        hover_data["velocity_km_s"] = ":.2f"
    if "owner" in df.columns:
        hover_data["owner"] = True
    if "object_type" in df.columns:
        hover_data["object_type"] = True
    if "starlink_group" in df.columns:
        hover_data["starlink_group"] = True

    fig = px.scatter_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        hover_name="object_name" if "object_name" in df.columns else None,
        hover_data=hover_data,
        custom_data=custom_cols if custom_cols else None,
        color=color_col,
        zoom=1,
        height=720,
    )

    fig.update_traces(marker={"size": 7, "opacity": 0.82})

    iss_df = pd.DataFrame()
    if "norad_id" in df.columns:
        iss_df = df[df["norad_id"] == 25544]

    if not iss_df.empty:
        fig.add_trace(
            go.Scattermapbox(
                lat=iss_df["latitude"],
                lon=iss_df["longitude"],
                mode="markers",
                marker={"size": 16, "color": "#f59e0b"},
                name="ISS",
                text=iss_df["object_name"] if "object_name" in iss_df.columns else None,
                hovertemplate="<b>%{text}</b><extra>ISS</extra>",
            )
        )

    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center={"lat": 15, "lon": 0},
            zoom=1,
            bounds={
                "west": -180,
                "east": 180,
                "south": -75,
                "north": 85,
            },
        ),
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor="#eef4fb",
        plot_bgcolor="#eef4fb",
        font={"color": "#0f172a"},
        legend={
            "orientation": "h",
            "y": 1.02,
            "x": 0,
            "bgcolor": "rgba(255,255,255,0.6)",
        },
    )

    desired_table_cols = [
        "norad_id",
        "object_name",
        "owner",
        "object_type",
        "altitude_km",
        "velocity_km_s",
        "starlink_group",
    ]
    available_table_cols = [c for c in desired_table_cols if c in df.columns]
    table_df = df[available_table_cols].copy()

    sort_cols = [c for c in ["altitude_km", "object_name"] if c in table_df.columns]
    if sort_cols:
        ascending = [False if c == "altitude_km" else True for c in sort_cols]
        table_df = table_df.sort_values(by=sort_cols, ascending=ascending)

    columns = [{"name": c, "id": c} for c in table_df.columns]

    total_satellites = len(df)
    avg_altitude = round(df["altitude_km"].dropna().mean(), 2) if "altitude_km" in df.columns else 0
    avg_velocity = round(df["velocity_km_s"].dropna().mean(), 2) if "velocity_km_s" in df.columns else 0
    owners_count = int(df["owner"].nunique()) if "owner" in df.columns else 0
    iss_present = "Yes" if not iss_df.empty else "No"

    kpis = [
        html.Div(className="kpi-card", children=[html.Span("Visible satellites"), html.H3(f"{total_satellites:,}")]),
        html.Div(className="kpi-card", children=[html.Span("Avg altitude (km)"), html.H3(f"{avg_altitude:,.2f}")]),
        html.Div(className="kpi-card", children=[html.Span("Avg velocity (km/s)"), html.H3(f"{avg_velocity:,.2f}")]),
        html.Div(className="kpi-card", children=[html.Span("ISS visible in data"), html.H3(iss_present)]),
        html.Div(className="kpi-card", children=[html.Span("Owners"), html.H3(f"{owners_count:,}")]),
    ]

    return fig, table_df.to_dict("records"), columns, kpis


@app.callback(
    Output("selected-satellite", "children"),
    Input("satellite-map", "clickData"),
)
def show_selected_satellite(click_data):
    if not click_data or "points" not in click_data:
        return html.Div(
            className="empty-state",
            children="Click a satellite on the map to inspect its details.",
        )

    point = click_data["points"][0]
    custom = point.get("customdata", [])
    name = point.get("hovertext", "Unknown")

    details = [
        html.Div(className="detail-item", children=[html.Span("Name"), html.Strong(name)]),
        html.Div(className="detail-item", children=[html.Span("NORAD"), html.Strong(custom[0] if len(custom) > 0 else "")]),
        html.Div(className="detail-item", children=[html.Span("Altitude (km)"), html.Strong(custom[1] if len(custom) > 1 else "")]),
        html.Div(className="detail-item", children=[html.Span("Velocity (km/s)"), html.Strong(custom[2] if len(custom) > 2 else "")]),
        html.Div(className="detail-item", children=[html.Span("Owner"), html.Strong(custom[3] if len(custom) > 3 else "")]),
        html.Div(className="detail-item", children=[html.Span("Type"), html.Strong(custom[4] if len(custom) > 4 else "")]),
    ]

    if len(custom) > 5:
        details.append(
            html.Div(
                className="detail-item",
                children=[html.Span("Starlink group"), html.Strong(custom[5] if custom[5] else "-")],
            )
        )

    return html.Div(className="details-grid", children=details)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)