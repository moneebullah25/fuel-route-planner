from django.contrib import admin

from .models import FuelStop, Station, Trip


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ["opis_id", "name", "city", "state", "retail_price"]
    list_filter = ["state"]
    search_fields = ["name", "city"]


class FuelStopInline(admin.TabularInline):
    model = FuelStop
    extra = 0


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ["id", "start_location", "finish_location", "distance_miles", "total_fuel_cost", "created_at"]
    readonly_fields = ["created_at", "route_geometry", "start_coords", "finish_coords"]
    inlines = [FuelStopInline]
