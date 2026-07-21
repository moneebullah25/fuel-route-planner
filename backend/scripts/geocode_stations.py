"""
One-off build step: turn the raw OPIS price CSV into a geocoded station list.

The OPIS file only has City/State (no coordinates), so we geocode each distinct
(city, state) to a centroid using pgeocode's offline GeoNames postal data — no
network geocoding API, no per-address calls. Canadian rows (AB/ON/BC/...) don't
match the US dataset and are dropped, which is correct for a USA-only planner.

Run:  uv run python scripts/geocode_stations.py
Output: api/data/stations.json  (committed; loaded by `manage.py load_stations`)
"""
import csv
import json
from pathlib import Path

import pgeocode

HERE = Path(__file__).resolve().parent.parent
RAW = HERE / "api" / "data" / "fuel-prices.csv"
OUT = HERE / "api" / "data" / "stations.json"


def build_city_lut() -> dict[str, tuple[float, float]]:
    nomi = pgeocode.Nominatim("us")
    d = nomi._data.dropna(subset=["latitude", "longitude", "place_name", "state_code"])
    key = d["place_name"].str.upper().str.strip() + "|" + d["state_code"].str.upper().str.strip()
    d = d.assign(_k=key)
    cent = d.groupby("_k")[["latitude", "longitude"]].mean()
    return {k: (float(r.latitude), float(r.longitude)) for k, r in cent.iterrows()}


def main() -> None:
    lut = build_city_lut()
    seen: set[int] = set()
    rows: list[dict] = []
    matched = missed = 0

    with RAW.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            city = (row["City"] or "").strip()
            state = (row["State"] or "").strip()
            coord = lut.get(f"{city.upper()}|{state.upper()}")
            if coord is None:
                missed += 1
                continue
            matched += 1
            opis = int(row["OPIS Truckstop ID"])
            if opis in seen:  # OPIS id repeats with alternate names — keep one
                continue
            seen.add(opis)
            lat, lon = coord
            rows.append({
                "opis_id": opis,
                "name": (row["Truckstop Name"] or "").strip(),
                "address": (row["Address"] or "").strip(),
                "city": city,
                "state": state,
                "price": float(row["Retail Price"]),
                "lat": round(lat, 5),
                "lon": round(lon, 5),
            })

    OUT.write_text(json.dumps(rows))
    print(f"rows matched={matched} missed={missed} unique_stations={len(rows)} -> {OUT}")


if __name__ == "__main__":
    main()
