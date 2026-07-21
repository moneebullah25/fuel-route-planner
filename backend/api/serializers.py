from rest_framework import serializers

from .models import FuelStop, Trip


class FuelStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = FuelStop
        fields = [
            "order", "name", "address", "city", "state", "coords",
            "mile_marker", "price_per_gallon", "gallons", "cost",
        ]


class TripSerializer(serializers.ModelSerializer):
    fuel_stops = FuelStopSerializer(many=True, read_only=True)

    class Meta:
        model = Trip
        fields = [
            "id",
            "start_location", "finish_location",
            "start_coords", "finish_coords",
            "distance_miles", "gallons_used", "total_fuel_cost",
            "route_geometry",
            "fuel_stops",
            "created_at",
        ]


class TripCreateSerializer(serializers.Serializer):
    start = serializers.CharField(max_length=500)
    finish = serializers.CharField(max_length=500)
