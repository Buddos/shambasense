from django.contrib import admin

from .models import Crop, Variety


class VarietyInline(admin.TabularInline):
    model = Variety
    extra = 1


@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "scientific_name",
        "crop_type",
        "is_active",
    )

    list_filter = (
        "crop_type",
        "is_active",
    )

    search_fields = (
        "name",
        "scientific_name",
    )

    ordering = ("name",)

    inlines = [VarietyInline]


@admin.register(Variety)
class VarietyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "crop",
        "maturity_days_min",
        "maturity_days_max",
        "is_active",
    )

    list_filter = (
        "crop",
        "is_active",
    )

    search_fields = (
        "name",
        "crop__name",
    )

    ordering = (
        "crop",
        "name",
    )