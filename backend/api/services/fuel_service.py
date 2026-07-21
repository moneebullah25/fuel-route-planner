"""
Fuel-stop planning.

Given a route polyline and the fuel stations near it, pick where to refuel so
that (a) we never exceed the vehicle's range and (b) total fuel cost is minimal.

Assumptions (from the assessment):
  - Max range           : 500 miles per tank
  - Fuel economy        : 10 miles per gallon  (=> 50 gal capacity)
  - We pay for every gallon the trip consumes (total_miles / 10).

Optimisation is the classic "gas station" greedy, which is provably cost-optimal
for a fixed route with known prices: at each fill, if a cheaper station is
reachable, buy just enough to get there; otherwise fill up and push on to the
cheapest station still in range.
"""
import math
from dataclasses import dataclass

from .route_service import haversine_miles

RANGE_MILES = 500.0
MPG = 10.0
CORRIDOR_MILES = 20.0   # a station this far (or less) off the route counts as "on the way"
SAMPLE_STEP_MILES = 5.0  # granularity for matching stations to a route position


class FuelPlanError(Exception):
    """Raised when the route cannot be fuelled within the vehicle's range."""


@dataclass
class RouteSample:
    mile: float
    lon: float
    lat: float


def cumulative_miles(geometry: list[list[float]]) -> list[float]:
    """Cumulative driving distance (miles) at each polyline vertex."""
    cum = [0.0]
    for i in range(1, len(geometry)):
        cum.append(cum[-1] + haversine_miles(geometry[i - 1], geometry[i]))
    return cum


def sample_route(geometry: list[list[float]], step: float = SAMPLE_STEP_MILES) -> list[RouteSample]:
    """Downsample the polyline to ~one point every `step` miles for fast station matching."""
    cum = cumulative_miles(geometry)
    samples: list[RouteSample] = []
    next_mark = 0.0
    for (lon, lat), mile in zip(geometry, cum):
        if mile >= next_mark:
            samples.append(RouteSample(mile=mile, lon=lon, lat=lat))
            next_mark += step
    last = geometry[-1]
    if not samples or samples[-1].mile < cum[-1]:
        samples.append(RouteSample(mile=cum[-1], lon=last[0], lat=last[1]))
    return samples


def stations_along_route(
    stations: list[dict],
    samples: list[RouteSample],
    corridor: float = CORRIDOR_MILES,
) -> list[dict]:
    """
    Keep stations within `corridor` miles of the route and tag each with its
    route mile-marker (position of the nearest sample). One entry per station.
    """
    if not samples:
        return []

    lats = [s.lat for s in samples]
    lons = [s.lon for s in samples]
    # Bounding box in degrees, padded generously for the corridor (~69 mi/deg lat).
    pad = corridor / 60.0
    min_lat, max_lat = min(lats) - pad, max(lats) + pad
    min_lon, max_lon = min(lons) - pad, max(lons) + pad

    out: list[dict] = []
    for st in stations:
        lat, lon = st["lat"], st["lon"]
        if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon):
            continue
        # Hot loop: find the nearest sample by cheap squared degree-distance (lon scaled
        # by cos(lat) so it is comparable to lat). Only the winner needs a real haversine.
        coslat = math.cos(math.radians(lat))
        best_d2 = float("inf")
        nearest = samples[0]
        for s in samples:
            dlat = lat - s.lat
            dlon = (lon - s.lon) * coslat
            d2 = dlat * dlat + dlon * dlon
            if d2 < best_d2:
                best_d2 = d2
                nearest = s
        if haversine_miles([lon, lat], [nearest.lon, nearest.lat]) <= corridor:
            out.append({**st, "mile": nearest.mile})
    out.sort(key=lambda c: c["mile"])
    return out


def plan_fuel_stops(
    candidates: list[dict],
    total_miles: float,
    tank_range: float = RANGE_MILES,
    mpg: float = MPG,
) -> tuple[list[dict], float]:
    """
    Choose refuel stops minimising total cost. Returns (stops, total_cost).
    `stops` are in travel order, each with gallons + cost bought there.
    Raises FuelPlanError if some leg exceeds the range.
    """
    pts = [c for c in candidates if 0.0 <= c["mile"] <= total_miles]
    if not pts:
        raise FuelPlanError("No fuel stations found within the route corridor.")

    if pts[0]["mile"] > tank_range:
        raise FuelPlanError(
            f"No fuel station within {tank_range:.0f} mi of the start "
            f"(nearest is at mile {pts[0]['mile']:.0f})."
        )
    # Fill up before departing at the price of the station nearest the origin, so every
    # gallon the trip burns is paid for. This is a virtual node at mile 0; the real
    # stations (including the nearest one) keep their true mile markers so inter-stop
    # distances — and the 500-mi range check — stay accurate.
    origin = {**pts[0], "mile": 0.0}
    fuel_pts = [origin] + pts
    n = len(fuel_pts)

    total_cost = 0.0
    tank = 0.0            # miles of fuel currently in the tank
    purchased = 0.0       # miles of fuel bought so far (cap at total_miles)
    bought: dict[int, float] = {}  # index -> miles of fuel bought there

    def buy(idx: int, miles_amount: float) -> None:
        nonlocal total_cost, tank, purchased
        miles_amount = min(miles_amount, total_miles - purchased)
        if miles_amount <= 1e-9:
            return
        total_cost += (miles_amount / mpg) * fuel_pts[idx]["price"]
        tank += miles_amount
        purchased += miles_amount
        bought[idx] = bought.get(idx, 0.0) + miles_amount

    i = 0
    while True:
        cur = fuel_pts[i]
        to_dest = total_miles - cur["mile"]
        window = [j for j in range(i + 1, n) if fuel_pts[j]["mile"] - cur["mile"] <= tank_range]
        cheaper = next((j for j in window if fuel_pts[j]["price"] < cur["price"]), None)

        if cheaper is not None:
            dist = fuel_pts[cheaper]["mile"] - cur["mile"]
            buy(i, dist - tank)
            target = cheaper
        elif to_dest <= tank_range:
            buy(i, to_dest - tank)
            break
        elif window:
            buy(i, tank_range - tank)
            target = min(window, key=lambda j: fuel_pts[j]["price"])
        else:
            gap = fuel_pts[i + 1]["mile"] - cur["mile"] if i + 1 < n else to_dest
            raise FuelPlanError(
                f"Fuel gap of {gap:.0f} mi after mile {cur['mile']:.0f} exceeds the "
                f"{tank_range:.0f} mi range."
            )

        tank -= (fuel_pts[target]["mile"] - cur["mile"])
        i = target

    stops: list[dict] = []
    for order, idx in enumerate(sorted(bought)):
        miles_amount = bought[idx]
        gallons = miles_amount / mpg
        pt = fuel_pts[idx]
        stops.append({
            "order": order,
            "name": pt["name"],
            "address": pt.get("address", ""),
            "city": pt["city"],
            "state": pt["state"],
            "coords": [pt["lon"], pt["lat"]],
            "mile_marker": round(pt["mile"], 1),
            "price_per_gallon": round(pt["price"], 3),
            "gallons": round(gallons, 2),
            "cost": round(gallons * pt["price"], 2),
        })
    return stops, round(total_cost, 2)
