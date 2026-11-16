from django.contrib import admin

from .models import Inspection


@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "planting_attempt",
        "inspection_date",
        "crop_stage",
        "crop_condition",
        "inspected_by",
    )

    list_filter = (
        "crop_stage",
        "crop_condition",
        "soil_moisture",
        "weed_pressure",
        "inspection_date",
    )

    search_fields = (
        "planting_attempt__crop__name",
        "planting_attempt__variety__name",
        "planting_attempt__field__name",
        "planting_attempt__field__farm__name",
        "inspected_by__username",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    date_hierarchy = "inspection_date"

    list_select_related = (
        "planting_attempt",
        "inspected_by",
    )
