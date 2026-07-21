import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import Station

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "stations.json"


class Command(BaseCommand):
    help = "Load geocoded fuel stations from api/data/stations.json into the database."

    def handle(self, *args, **options):
        if not DATA_FILE.exists():
            self.stderr.write(f"Missing {DATA_FILE}. Run scripts/geocode_stations.py first.")
            return

        rows = json.loads(DATA_FILE.read_text())
        with transaction.atomic():
            Station.objects.all().delete()
            Station.objects.bulk_create(
                [
                    Station(
                        opis_id=r["opis_id"],
                        name=r["name"],
                        address=r["address"],
                        city=r["city"],
                        state=r["state"],
                        retail_price=r["price"],
                        lat=r["lat"],
                        lon=r["lon"],
                    )
                    for r in rows
                ],
                batch_size=1000,
            )
        self.stdout.write(self.style.SUCCESS(f"Loaded {len(rows)} stations."))
