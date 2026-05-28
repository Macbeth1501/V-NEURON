"""
pipeline.py — Unified V-NEURON data build pipeline.

Replaces scripts 02 → 14. Run this once to generate all graph files.

Usage:
    python pipeline.py              # Run full pipeline
    python pipeline.py --step 3     # Run from step 3 onwards
    python pipeline.py --only db    # Only push data to DB
"""
import argparse
import os
import certifi
import osmnx as ox
import geopandas as gpd
import networkx as nx
from sqlalchemy import create_engine, text

import config

# ── SSL Fix (prevents OSM download failures on some systems) ──────────────────
os.environ["SSL_CERT_FILE"]      = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
os.environ["CURL_CA_BUNDLE"]     = certifi.where()
os.makedirs(config.DATA_DIR, exist_ok=True)


def _get_db_engine():
    url = config.DATABASE_URL
    if not url:
        raise ValueError("DATABASE_URL is not set in your .env file.")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return create_engine(url)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Download Road Network
# ─────────────────────────────────────────────────────────────────────────────
def step1_download_roads():
    print("\n[STEP 1] Downloading Nagpur road network from OpenStreetMap...")
    G = ox.graph_from_point(config.CENTER_LATLON, dist=config.RADIUS_M, network_type="drive")
    print(f"  Nodes: {len(G.nodes):,}  |  Edges: {len(G.edges):,}")
    ox.save_graphml(G, filepath=config.ROADS_GRAPHML)
    print(f"  ✅ Saved → {config.ROADS_GRAPHML}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Download Transit Data (Metro + Bus)
# ─────────────────────────────────────────────────────────────────────────────
def step2_download_transit():
    print("\n[STEP 2] Fetching transit data (metro + bus)...")
    metro = ox.features_from_point(
        config.CENTER_LATLON,
        dist=config.RADIUS_M,
        tags={"railway": ["subway", "light_rail", "station", "construction", "proposed"]},
    )
    bus = ox.features_from_point(
        config.CENTER_LATLON,
        dist=config.RADIUS_M,
        tags={
            "highway": ["bus_stop", "platform"],
            "public_transport": ["stop_position", "platform", "station"],
            "amenity": "bus_station",
        },
    )
    metro_stations = metro[metro.geom_type == "Point"]
    print(f"  Metro features: {len(metro):,}  |  Confirmed stations: {len(metro_stations):,}")
    print(f"  Bus features:   {len(bus):,}")
    metro.to_file(config.METRO_GEOJSON,  driver="GeoJSON")
    bus.to_file(config.BUS_GEOJSON,      driver="GeoJSON")
    print(f"  ✅ Saved → {config.METRO_GEOJSON}, {config.BUS_GEOJSON}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Push raw layers to Supabase/PostGIS
# ─────────────────────────────────────────────────────────────────────────────
def step3_push_to_db():
    print("\n[STEP 3] Pushing raw layers to Supabase/PostGIS...")
    if not config.DATABASE_URL:
        print("  ⚠ DATABASE_URL not set. Skipping Step 3 (Database upload).")
        return
    engine = _get_db_engine()

    # Enable PostGIS extension (safe to run if already enabled)
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.execute(text("COMMIT;"))
    print("  PostGIS extension ready.")

    G = ox.load_graphml(config.ROADS_GRAPHML)
    nodes, edges = ox.graph_to_gdfs(G)
    edges.to_postgis("nagpur_roads",       engine, if_exists="replace")
    nodes.to_postgis("nagpur_road_nodes",  engine, if_exists="replace")
    metro = gpd.read_file(config.METRO_GEOJSON)
    bus   = gpd.read_file(config.BUS_GEOJSON)
    metro.to_postgis("nagpur_metro", engine, if_exists="replace")
    bus.to_postgis("nagpur_bus",     engine, if_exists="replace")
    print("  ✅ Road network, metro, and bus layers pushed to database.")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Project all layers to UTM (EPSG:32644)
# ─────────────────────────────────────────────────────────────────────────────
def step4_project_layers():
    print("\n[STEP 4] Projecting all layers to UTM (EPSG:32644)...")
    G = ox.load_graphml(config.ROADS_GRAPHML)
    G_proj = ox.project_graph(G, to_crs=config.CRS_PROJECTED)
    # Add speed/travel_time on the projected graph
    G_proj = ox.routing.add_edge_speeds(G_proj, hwy_speeds=config.SPEEDS_FREE_FLOW)
    G_proj = ox.routing.add_edge_travel_times(G_proj)
    ox.save_graphml(G_proj, filepath=config.ROADS_PROJECTED)

    metro = gpd.read_file(config.METRO_GEOJSON).to_crs(config.CRS_PROJECTED)
    bus   = gpd.read_file(config.BUS_GEOJSON).to_crs(config.CRS_PROJECTED)
    metro.to_file(config.METRO_PROJ_GEOJSON, driver="GeoJSON")
    bus.to_file(config.BUS_PROJ_GEOJSON,     driver="GeoJSON")
    print(f"  ✅ Projected graph CRS: {G_proj.graph.get('crs', 'EPSG:32644')}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Push projected layers + spatial indexes to Supabase
# ─────────────────────────────────────────────────────────────────────────────
def step5_finalize_db():
    print("\n[STEP 5] Pushing projected layers and creating spatial indexes...")
    if not config.DATABASE_URL:
        print("  ⚠ DATABASE_URL not set. Skipping Step 5 (Database upload).")
        return
    engine = _get_db_engine()
    metro_proj = gpd.read_file(config.METRO_PROJ_GEOJSON)
    bus_proj   = gpd.read_file(config.BUS_PROJ_GEOJSON)
    metro_proj.to_postgis("nagpur_metro_projected", engine, if_exists="replace")
    bus_proj.to_postgis("nagpur_bus_projected",     engine, if_exists="replace")
    with engine.connect() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_metro_geom ON nagpur_metro_projected USING GIST (geometry);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_bus_geom   ON nagpur_bus_projected   USING GIST (geometry);"))
        conn.execute(text("COMMIT;"))
    print("  ✅ Projected layers pushed + spatial indexes created.")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — Snap metro stations to road network (multimodal base)
# ─────────────────────────────────────────────────────────────────────────────
def step6_snap_metro_stations():
    print("\n[STEP 6] Connecting metro stations to road network...")
    G = ox.load_graphml(config.ROADS_PROJECTED)
    metro_gdf = gpd.read_file(config.METRO_PROJ_GEOJSON)
    stations  = metro_gdf[metro_gdf.geom_type == "Point"].copy().reset_index(drop=True)
    metro_speed_mps = (config.METRO_SPEED_KMH * 1000) / 3600

    connected = 0
    for idx, station in stations.iterrows():
        nearest = ox.distance.nearest_nodes(G, X=station.geometry.x, Y=station.geometry.y)
        dist_m  = ox.distance.euclidean(
            station.geometry.y, station.geometry.x,
            G.nodes[nearest]["y"],  G.nodes[nearest]["x"],
        )
        walk_time = dist_m / config.WALKING_SPEED_MPS
        node_id   = config.METRO_ID_BASE + idx
        name      = station.get("name", f"Station_{idx}")

        G.add_node(node_id, x=station.geometry.x, y=station.geometry.y,
                   highway="metro_station", name=name)
        G.add_edge(node_id, nearest, length=dist_m, travel_time=walk_time, highway="footway")
        G.add_edge(nearest, node_id, length=dist_m, travel_time=walk_time, highway="footway")
        connected += 1

    ox.save_graphml(G, filepath=config.MULTIMODAL_BASE)
    print(f"  ✅ {connected} metro stations connected → {config.MULTIMODAL_BASE}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 7 — Add metro rail logic (Orange + Aqua lines)
# ─────────────────────────────────────────────────────────────────────────────
def step7_add_metro_lines():
    print("\n[STEP 7] Adding Nagpur Metro rail logic (Orange + Aqua lines)...")
    G = ox.load_graphml(config.MULTIMODAL_BASE)
    metro_speed_mps = (config.METRO_SPEED_KMH * 1000) / 3600
    name_to_node = {
        data["name"]: node
        for node, data in G.nodes(data=True)
        if data.get("highway") == "metro_station"
    }

    def _add_line(stations, line_name):
        added = 0
        for i in range(len(stations) - 1):
            u_name, v_name = stations[i], stations[i + 1]
            if u_name in name_to_node and v_name in name_to_node:
                u, v    = name_to_node[u_name], name_to_node[v_name]
                dist_m  = ox.distance.euclidean(
                    G.nodes[u]["y"], G.nodes[u]["x"],
                    G.nodes[v]["y"], G.nodes[v]["x"],
                )
                tt = dist_m / metro_speed_mps
                G.add_edge(u, v, length=dist_m, travel_time=tt, highway="subway", name=line_name)
                G.add_edge(v, u, length=dist_m, travel_time=tt, highway="subway", name=line_name)
                added += 1
            else:
                missing = [s for s in (u_name, v_name) if s not in name_to_node]
                print(f"    ⚠ Stations not found in graph: {missing}")
        print(f"  {line_name}: {added} rail segments added.")

    _add_line(config.ORANGE_LINE, "Orange Line")
    _add_line(config.AQUA_LINE,   "Aqua Line")
    ox.save_graphml(G, filepath=config.OMNIMODAL_FINAL)
    print(f"  ✅ Final omnimodal graph saved → {config.OMNIMODAL_FINAL}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 8 — Generate Peak-Hour Calibrated Network
# ─────────────────────────────────────────────────────────────────────────────
def step8_calibrate_peak_hour():
    print("\n[STEP 8] Generating peak-hour calibrated network...")
    G = ox.load_graphml(config.OMNIMODAL_FINAL)

    # Apply boarding penalty to all transit transfer (footway) edges
    penalty_applied = 0
    for u, v, k, data in G.edges(data=True, keys=True):
        if data.get("highway") == "footway":
            data["travel_time"] = data.get("travel_time", 0) + config.BOARDING_PENALTY_S
            penalty_applied += 1

    # Apply congested road speeds
    G = ox.routing.add_edge_speeds(G, hwy_speeds=config.SPEEDS_PEAK_HOUR)
    G = ox.routing.add_edge_travel_times(G)

    ox.save_graphml(G, filepath=config.CALIBRATED_NETWORK)
    print(f"  Boarding penalty ({config.BOARDING_PENALTY_S}s) applied to {penalty_applied} transfer edges.")
    print(f"  ✅ Calibrated peak-hour network saved → {config.CALIBRATED_NETWORK}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 9 — Verification audit
# ─────────────────────────────────────────────────────────────────────────────
def step9_audit():
    import geopandas as gpd
    from shapely.geometry import Point

    print("\n[STEP 9] Running comparative audit (SVPCET → Automotive Square)...")
    orig = (21.056, 79.027)
    dest = (21.203, 79.083)

    orig_gs = gpd.GeoSeries([Point(orig[1], orig[0])], crs="EPSG:4326").to_crs(config.CRS_PROJECTED)
    dest_gs = gpd.GeoSeries([Point(dest[1], dest[0])], crs="EPSG:4326").to_crs(config.CRS_PROJECTED)

    results = []
    for label, path in [("Off-Peak", config.OMNIMODAL_FINAL), ("Peak Hour", config.CALIBRATED_NETWORK)]:
        G = ox.load_graphml(path)
        on = ox.distance.nearest_nodes(G, X=orig_gs[0].x, Y=orig_gs[0].y)
        dn = ox.distance.nearest_nodes(G, X=dest_gs[0].x, Y=dest_gs[0].y)
        try:
            route   = nx.shortest_path(G, on, dn, weight="travel_time")
            dist_km = nx.path_weight(G, route, weight="length") / 1000
            time_mn = nx.path_weight(G, route, weight="travel_time") / 60
            results.append(f"  {label:10s} → {dist_km:.2f} km | {time_mn:.1f} min")
        except nx.NetworkXNoPath:
            results.append(f"  {label:10s} → No path found")

    for r in results:
        print(r)
    print("  ✅ Audit complete.")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
STEPS = {
    1: step1_download_roads,
    2: step2_download_transit,
    3: step3_push_to_db,
    4: step4_project_layers,
    5: step5_finalize_db,
    6: step6_snap_metro_stations,
    7: step7_add_metro_lines,
    8: step8_calibrate_peak_hour,
    9: step9_audit,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="V-NEURON Data Pipeline")
    parser.add_argument("--from-step", type=int, default=1, metavar="N",
                        help="Start pipeline from step N (default: 1)")
    parser.add_argument("--only-step", type=int, default=None, metavar="N",
                        help="Run only step N")
    args = parser.parse_args()

    print("=" * 60)
    print("  V-NEURON Data Build Pipeline")
    print("=" * 60)

    if args.only_step:
        steps_to_run = [args.only_step]
    else:
        steps_to_run = [s for s in sorted(STEPS.keys()) if s >= args.from_step]

    for n in steps_to_run:
        if n not in STEPS:
            print(f"  ❌ Unknown step: {n}")
            continue
        try:
            STEPS[n]()
        except Exception as e:
            print(f"\n  ❌ Step {n} failed: {e}")
            print("  Fix the issue and re-run with --from-step", n)
            raise SystemExit(1)

    print("\n" + "=" * 60)
    print("  ✅ Pipeline complete!")
    print("=" * 60)
