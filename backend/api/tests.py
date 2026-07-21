"""
Unit tests for the fuel-planning logic and route geometry helpers.
Run with: python manage.py test api
"""
from django.test import SimpleTestCase

from .services.fuel_service import (
    FuelPlanError,
    cumulative_miles,
    plan_fuel_stops,
    sample_route,
    stations_along_route,
)
from .services.route_service import haversine_miles


def station(mile, price, name="S"):
    # A candidate already projected onto the route (mile + price is all the planner needs).
    return {"mile": mile, "price": price, "name": name, "address": "", "city": "C",
            "state": "XX", "lat": 0.0, "lon": 0.0}


class HaversineTests(SimpleTestCase):
    def test_known_distance(self):
        # NYC (-74.006, 40.7128) to LA (-118.2437, 34.0522) ~ 2450 mi great-circle.
        d = haversine_miles([-74.006, 40.7128], [-118.2437, 34.0522])
        self.assertAlmostEqual(d, 2450, delta=60)

    def test_zero(self):
        self.assertEqual(haversine_miles([1.0, 1.0], [1.0, 1.0]), 0.0)


class RouteGeometryTests(SimpleTestCase):
    def test_cumulative_monotonic(self):
        geom = [[-100.0, 40.0], [-99.0, 40.0], [-98.0, 40.0]]
        cum = cumulative_miles(geom)
        self.assertEqual(cum[0], 0.0)
        self.assertTrue(cum[1] < cum[2])

    def test_sample_endpoints(self):
        geom = [[-100.0 + i * 0.1, 40.0] for i in range(50)]
        samples = sample_route(geom, step=5.0)
        self.assertEqual(samples[0].mile, 0.0)
        self.assertAlmostEqual(samples[-1].mile, cumulative_miles(geom)[-1], places=3)


class CorridorMatchingTests(SimpleTestCase):
    def test_keeps_near_route_drops_far(self):
        # East-west route along lat 40. A station ~5 mi off stays; one ~2 degrees
        # (~100+ mi) off is dropped. The kept one is tagged with a route mile-marker.
        geom = [[-100.0 + i * 0.1, 40.0] for i in range(30)]  # ~160 mi run
        samples = sample_route(geom, step=5.0)
        near = {"lat": 40.05, "lon": -99.0, "name": "near", "address": "", "city": "C", "state": "XX", "price": 3.0}
        far = {"lat": 42.0, "lon": -99.0, "name": "far", "address": "", "city": "C", "state": "XX", "price": 3.0}
        out = stations_along_route([near, far], samples, corridor=20.0)
        names = {c["name"] for c in out}
        self.assertIn("near", names)
        self.assertNotIn("far", names)
        self.assertGreater(out[0]["mile"], 0.0)


class FuelPlanTests(SimpleTestCase):
    def test_gallons_equal_consumption(self):
        # 900 mi trip => exactly 90 gallons purchased regardless of prices.
        cands = [station(m, 3.0) for m in (0, 400, 800)]
        stops, cost = plan_fuel_stops(cands, total_miles=900)
        gallons = sum(s["gallons"] for s in stops)
        self.assertAlmostEqual(gallons, 90.0, places=1)
        self.assertAlmostEqual(cost, 270.0, delta=1.0)

    def test_prefers_cheaper_station(self):
        # $4 at the start, $2 at mile 50. Optimal: buy just 5 gal @ $4 to reach the
        # cheap station (you can't get there on empty), then the remaining 25 gal @ $2.
        cands = [station(0, 4.00, "pricey"), station(50, 2.00, "cheap")]
        stops, cost = plan_fuel_stops(cands, total_miles=300)
        self.assertAlmostEqual(cost, 5 * 4.00 + 25 * 2.00, delta=1.0)
        self.assertLess(cost, 30 * 4.00)  # cheaper than buying it all at the start

    def test_buy_just_enough_before_cheaper(self):
        # Expensive at start, much cheaper at mile 400 (within range): buy minimum
        # to reach the cheap one, then the rest cheaply.
        cands = [station(0, 5.00, "start"), station(400, 2.00, "cheap")]
        stops, cost = plan_fuel_stops(cands, total_miles=800)
        # 40 gal @ $5 to cover 0->400, 40 gal @ $2 to cover 400->800 = 200 + 80 = 280.
        self.assertAlmostEqual(cost, 280.0, delta=2.0)
        naive_all_expensive = 80 * 5.00
        self.assertLess(cost, naive_all_expensive)

    def test_first_station_not_at_origin(self):
        # Nearest station is 100 mi in; the 0->100 leg must still be paid for,
        # so total gallons == consumption and avg price never dips below the min.
        cands = [station(100, 3.0), station(450, 3.0)]
        stops, cost = plan_fuel_stops(cands, total_miles=800)
        gallons = sum(s["gallons"] for s in stops)
        self.assertAlmostEqual(gallons, 80.0, places=1)
        self.assertAlmostEqual(cost, 240.0, delta=1.0)
        self.assertGreaterEqual(cost / gallons, 3.0)

    def test_far_origin_unequal_prices_no_overbuy(self):
        # Nearest station is 300 mi in and cheap ($2); a pricey one ($5) sits before the
        # finish. Must not overpay by charging the 0->300 leg at the wrong distance, and
        # must still reach the finish (the 300-mi station is a real refuel point).
        cands = [station(300, 2.00, "cheap"), station(700, 5.00, "pricey")]
        stops, cost = plan_fuel_stops(cands, total_miles=1000)
        gallons = sum(s["gallons"] for s in stops)
        self.assertAlmostEqual(gallons, 100.0, places=1)  # full consumption paid
        self.assertGreaterEqual(cost / gallons, 2.00)     # never below the min price

    def test_range_gap_raises(self):
        # 700 mi apart > 500 range => infeasible.
        cands = [station(0, 3.0), station(700, 3.0)]
        with self.assertRaises(FuelPlanError):
            plan_fuel_stops(cands, total_miles=1200)

    def test_no_station_near_start_raises(self):
        cands = [station(600, 3.0)]
        with self.assertRaises(FuelPlanError):
            plan_fuel_stops(cands, total_miles=1000)

    def test_empty_candidates_raises(self):
        with self.assertRaises(FuelPlanError):
            plan_fuel_stops([], total_miles=100)
