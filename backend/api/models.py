from django.db import models


class Station(models.Model):
    """A fuel station from the OPIS price list, geocoded to a city centroid."""
    opis_id = models.IntegerField(db_index=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=500, blank=True)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=10)
    retail_price = models.FloatField()
    lat = models.FloatField()
    lon = models.FloatField()

    class Meta:
        indexes = [models.Index(fields=["lat", "lon"])]

    def __str__(self):
        return f"{self.name} ({self.city}, {self.state}) ${self.retail_price:.3f}"


class Trip(models.Model):
    """A single start→finish routing query and its computed fuel plan."""
    start_location = models.CharField(max_length=500)
    finish_location = models.CharField(max_length=500)

    start_coords = models.JSONField()   # [lon, lat]
    finish_coords = models.JSONField()  # [lon, lat]

    distance_miles = models.FloatField()
    gallons_used = models.FloatField()
    total_fuel_cost = models.FloatField()

    # Route polyline as a list of [lon, lat] pairs (GeoJSON coordinate order).
    route_geometry = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Trip {self.id}: {self.start_location} → {self.finish_location}"


class FuelStop(models.Model):
    """A planned refuel along a trip, in travel order."""
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="fuel_stops")
    order = models.IntegerField(default=0)

    name = models.CharField(max_length=255)
    address = models.CharField(max_length=500, blank=True)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=10)
    coords = models.JSONField()  # [lon, lat]

    mile_marker = models.FloatField()
    price_per_gallon = models.FloatField()
    gallons = models.FloatField()
    cost = models.FloatField()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"Stop {self.order}: {self.name} @ mile {self.mile_marker:.0f}"
