"""
routing_engine.py — V-NEURON core routing logic.

The graphs are loaded once (via @st.cache_resource) and shared across all
Streamlit sessions, keeping memory usage constant regardless of user count.
"""
from __future__ import annotations

import osmnx as ox
import networkx as nx
import geopandas as gpd
from shapely.geometry import Point
from typing import Optional
import streamlit as st

import config


# ─────────────────────────────────────────────────────────────────────────────
# Graph loader — cached at process level, not per-session
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading routing graph…")
def load_graph(path: str):
    """Load a GraphML file once and keep it in shared process memory."""
    return ox.load_graphml(path)


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────
def _project_point(lat: float, lon: float) -> tuple[float, float]:
    """Reproject a WGS-84 (lat, lon) point to the project CRS. Returns (x, y)."""
    gs = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(config.CRS_PROJECTED)
    return gs[0].x, gs[0].y


def _nearest_node(G, x: float, y: float) -> int:
    """Find the nearest graph node to a projected (x, y) coordinate."""
    return ox.distance.nearest_nodes(G, X=x, Y=y)


def _modal_split(route_gdf: gpd.GeoDataFrame) -> list[dict]:
    """Summarise distance and travel time per transport mode in a route."""
    grp = (
        route_gdf.groupby("highway")
        .agg(length=("length", "sum"), travel_time=("travel_time", "sum"))
        .reset_index()
    )
    return [
        {
            "mode":     row["highway"],
            "dist_km":  round(row["length"] / 1000, 2),
            "time_min": round(row["travel_time"] / 60, 1),
        }
        for _, row in grp.iterrows()
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
def get_route(
    orig_lat: float,
    orig_lon: float,
    dest_lat: float,
    dest_lon: float,
    scenario: str = "off_peak",   # "off_peak" | "peak_hour"
) -> Optional[dict]:
    """
    Compute the optimal multimodal route between two GPS coordinates.

    Parameters
    ----------
    orig_lat, orig_lon : float  — WGS-84 origin coordinates
    dest_lat, dest_lon : float  — WGS-84 destination coordinates
    scenario           : str    — "off_peak" or "peak_hour"

    Returns
    -------
    dict with keys:
        dist_km, time_min, modal_split, route_gdf, transfers
    or None if no path exists.
    """
    graph_path = (
        config.CALIBRATED_NETWORK if scenario == "peak_hour"
        else config.OMNIMODAL_FINAL
    )
    G = load_graph(graph_path)

    # Project origin & destination to graph CRS
    orig_x, orig_y = _project_point(orig_lat, orig_lon)
    dest_x, dest_y = _project_point(dest_lat, dest_lon)

    orig_node = _nearest_node(G, orig_x, orig_y)
    dest_node = _nearest_node(G, dest_x, dest_y)

    try:
        route = nx.shortest_path(G, orig_node, dest_node, weight="travel_time")
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None

    route_gdf = ox.routing.route_to_gdf(G, route)
    dist_km   = nx.path_weight(G, route, weight="length") / 1000
    time_min  = nx.path_weight(G, route, weight="travel_time") / 60
    transfers = len(route_gdf[route_gdf["highway"] == "footway"])

    return {
        "dist_km":     round(dist_km, 2),
        "time_min":    round(time_min, 1),
        "modal_split": _modal_split(route_gdf),
        "route_gdf":   route_gdf,
        "transfers":   transfers,
    }
