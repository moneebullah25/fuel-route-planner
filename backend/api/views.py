import logging
from functools import lru_cache

from django.http import Http404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import FuelStop, Station, Trip
from .serializers import TripCreateSerializer, TripSerializer
from .services.fuel_service import (
    MPG,
    FuelPlanError,
    plan_fuel_stops,
    sample_route,
    stations_along_route,
)
from .services.route_service import geocode, get_route

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _all_stations() -> tuple[dict, ...]:
    """Reference data — load once into memory (immutable tuple, safe to cache)."""
    return tuple(
        Station.objects.values("name", "address", "city", "state", "retail_price", "lat", "lon")
    )


def _station_dicts() -> list[dict]:
    return [{**s, "price": s["retail_price"]} for s in _all_stations()]


@api_view(["GET"])
def health(request):
    return Response({"status": "ok", "stations_loaded": Station.objects.count()})


@api_view(["POST"])
def create_trip(request):
    serializer = TripCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    start_q = serializer.validated_data["start"]
    finish_q = serializer.validated_data["finish"]

    # Geocode start + finish: 2 Nominatim calls.
    try:
        start_coords = geocode(start_q)
        finish_coords = geocode(finish_q)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        logger.exception("Geocoding error")
        return Response(
            {"error": "Location lookup is temporarily unavailable. Please try again."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    # One OSRM call for the whole route polyline.
    try:
        route = get_route(start_coords, finish_coords)
    except Exception:
        logger.exception("Routing error")
        return Response(
            {"error": "Could not compute a driving route between those locations."},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    distance_miles = route["distance_miles"]
    geometry = route["geometry"]

    # Fuel plan — entirely in-memory, no external calls.
    try:
        samples = sample_route(geometry)
        # Sample miles come from haversine chord-sums; scale them into OSRM road-mile
        # space so station positions, the 500-mi range check, and gallons all agree.
        chord_total = samples[-1].mile if samples else 0.0
        if chord_total > 0:
            scale = distance_miles / chord_total
            for s in samples:
                s.mile *= scale
        candidates = stations_along_route(_station_dicts(), samples)
        stops, total_cost = plan_fuel_stops(candidates, distance_miles)
    except FuelPlanError as e:
        return Response({"error": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    gallons_used = round(distance_miles / MPG, 2)

    trip = Trip.objects.create(
        start_location=start_q,
        finish_location=finish_q,
        start_coords=start_coords,
        finish_coords=finish_coords,
        distance_miles=distance_miles,
        gallons_used=gallons_used,
        total_fuel_cost=total_cost,
        route_geometry=geometry,
    )
    FuelStop.objects.bulk_create([FuelStop(trip=trip, **s) for s in stops])

    return Response(TripSerializer(trip).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def get_trip(request, trip_id):
    try:
        trip = Trip.objects.prefetch_related("fuel_stops").get(pk=trip_id)
    except Trip.DoesNotExist:
        raise Http404
    return Response(TripSerializer(trip).data)
