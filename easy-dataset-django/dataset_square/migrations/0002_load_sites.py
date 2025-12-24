from django.db import migrations


def load_sites(apps, schema_editor):
    Site = apps.get_model("dataset_square", "Site")
    import os
    import json
    from django.conf import settings

    path = os.path.join(settings.BASE_DIR, "constant", "sites.json")
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    created = 0
    for item in data:
        link = item.get("link") or ""
        defaults = {
            "name": item.get("name", ""),
            "description": item.get("description", "") or "",
            "image": item.get("image", "") or "",
            "labels": item.get("labels", []) or [],
        }
        obj, is_created = Site.objects.update_or_create(link=link, defaults=defaults)
        if is_created:
            created += 1


def unload_sites(apps, schema_editor):
    # 不在回滚时删除数据
    return


class Migration(migrations.Migration):

    dependencies = [
        ("dataset_square", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(load_sites, reverse_code=migrations.RunPython.noop),
    ]


