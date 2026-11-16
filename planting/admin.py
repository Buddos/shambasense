
from django.contrib import admin

from .models import PlantingAttempt


@admin.register(PlantingAttempt)
class PlantingAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "crop",
        "variety",
        "field",
        "planting_date",
        "expected_season_end_date",
        "area_planted",
        "planting_method",
        "status",
    )

    list_filter = (
        "crop",
        "planting_method",
        "status",
        "planting_date",
    )

    search_fields = (
        "crop__name",
        "variety__name",
        "field__name",
        "field__farm__name",
        "seed_source",
    )

    date_hierarchy = "planting_date"

    list_select_related = (
        "crop",
        "variety",
        "field",
        "field__farm",
    )