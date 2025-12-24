import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from dataset_square.models import Site


class Command(BaseCommand):
    help = "Import dataset-square sites from constant/sites.json into database"

    def handle(self, *args, **options):
        src = os.path.join(settings.BASE_DIR, "constant", "sites.json")
        if not os.path.exists(src):
            self.stdout.write(self.style.ERROR(f"File not found: {src}"))
            return

        with open(src, "r", encoding="utf-8") as f:
            data = json.load(f)

        created = 0
        updated = 0
        for item in data:
            obj, is_created = Site.objects.update_or_create(
                link=item.get("link"),
                defaults={
                    "name": item.get("name", ""),
                    "description": item.get("description", ""),
                    "image": item.get("image", ""),
                    "labels": item.get("labels", []),
                },
            )
            if is_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Imported: created={created}, updated={updated}"))


