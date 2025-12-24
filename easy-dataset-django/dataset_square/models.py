from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone


class Site(models.Model):
    name = models.CharField(max_length=255)
    link = models.URLField(max_length=1024)
    description = models.TextField(blank=True, default="")
    image = models.CharField(max_length=1024, blank=True, default="")
    labels = ArrayField(models.CharField(max_length=64), default=list, blank=True)
    create_at = models.DateTimeField(default=timezone.now)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "dataset_square_sites"
        ordering = ["-create_at"]

    def __str__(self):
        return self.name


