from django.contrib import admin
from .models import Site


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "link", "create_at", "update_at")
    search_fields = ("name", "link", "labels")
    list_filter = ()


