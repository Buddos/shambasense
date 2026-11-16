from django.contrib import admin

from .models import Farm, Field


class FieldInline(admin.TabularInline):
    model = Field
    extra = 0


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "county",
        "sub_county",
        "total_acreage",
        "created_at",
    )

    list_filter = (
        "county",
        "sub_county",
    )

    search_fields = (
        "name",
        "owner__username",
        "owner__email",
        "county",
        "sub_county",
        "ward",
        "village",
    )

    ordering = ("name",)

    inlines = [FieldInline]


@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "farm",
        "acreage",
        "soil_type",
        "created_at",
    )

    list_filter = (
        "soil_type",
        "farm__county",
    )

    search_fields = (
        "name",
        "farm__name",
        "farm__owner__username",
    )

    ordering = ("farm", "name")