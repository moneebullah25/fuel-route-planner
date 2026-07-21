"""
Routing + geocoding.

External calls per request:
  - Nominatim geocoding: 2 (start + finish) — a geocoder, not the routing API.
  - OSRM routing: 1 (single call for the whole polyline).

OSRM's public demo server (router.project-osrm.org) is free and needs no API key.
"""
import math
import os
import time
from functools import lru_cache

import requests

OSRM_BASE = os.getenv("OSRM_BASE", "https://router.project-osrm.org")
NOMINATIM_BASE = os.getenv("NOMINATIM_BASE", "https://nominatim.openstreetmap.org")
HEADERS = {"User-Agent": "FuelRoutePlanner/1.0 (assessment)"}

EARTH_RADIUS_MI = 3958.8

_last_geocode_at = 0.0  # module-global throttle for Nominatim's 1 req/sec policy


def haversine_miles(a: list[float], b: list[float]) -> float:
    """Great-circle distance in miles between two [lon, lat] points."""
    lon1, lat1 = math.radians(a[0]), math.radians(a[1])
    lon2, lat2 = math.radians(b[0]), math.radians(b[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_MI * math.asin(math.sqrt(h))


@lru_cache(maxsize=1024)
def geocode(address: str) -> list[float]:
    """Geocode a US address/place to [lon, lat] via Nominatim. Raises ValueError if not found.

    Cached: repeat lookups of the same place skip the network call and the throttle.
    Callers treat the returned list as read-only (the same object is shared across hits).
    """
    global _last_geocode_at
    wait = 1.0 - (time.monotonic() - _last_geocode_at)  # only throttle back-to-back calls
    if wait > 0:
        time.sleep(wait)
    _last_geocode_at = time.monotonic()
    resp = requests.get(
        f"{NOMINATIM_BASE}/search",
        params={"q": address, "format": "json", "limit": 1, "countrycodes": "us"},
        headers=HEADERS,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data:
        raise ValueError(f"Could not find a US location for: {address!r}")
    return [float(data[0]["lon"]), float(data[0]["lat"])]


def get_route(start: list[float], finish: list[float]) -> dict:
    """
    Single OSRM call for the driving route between two [lon, lat] points.
    Returns {distance_miles, geometry: [[lon, lat], ...]}. Result is cached and
    treated as read-only by callers.
    """
    return _get_route_cached(tuple(start), tuple(finish))


@lru_cache(maxsize=512)
def _get_route_cached(start: tuple[float, float], finish: tuple[float, float]) -> dict:
    coords = f"{start[0]},{start[1]};{finish[0]},{finish[1]}"
    resp = requests.get(
        f"{OSRM_BASE}/route/v1/driving/{coords}",
        # 'full' geometry: cumulative_miles sums haversine chords over every vertex, so
        # accurate per-leg distances (the 500-mi check) and corridor station matching need
        # the detailed polyline. The call is cached, so the payload is paid once per route.
        params={"overview": "full", "geometries": "geojson", "alternatives": "false", "steps": "false"},
        headers=HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError(f"OSRM could not route between the given points: {data.get('code')}")

    route = data["routes"][0]
    return {
        "distance_miles": round(route["distance"] / 1609.344, 2),  # meters → miles
        "geometry": route["geometry"]["coordinates"],  # list of [lon, lat]
    }
