from django.contrib import admin

from .models import (
    EstablishmentAssessment,
    RemainingSeasonAssessment,
)


@admin.register(EstablishmentAssessment)
class EstablishmentAssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "inspection",
        "status",
        "emergence_percentage",
        "rule_version",
        "assessed_at",
    )

    list_filter = (
        "status",
        "rule_version",
        "assessed_at",
    )

    search_fields = (
        "inspection__planting_attempt__crop__name",
        "inspection__planting_attempt__variety__name",
        "inspection__planting_attempt__field__farm__name",
    )

    readonly_fields = (
        "assessed_at",
        "created_at",
    )


@admin.register(RemainingSeasonAssessment)
class RemainingSeasonAssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "planting_attempt",
        "status",
        "assessment_date",
        "expected_maturity_start",
        "expected_maturity_end",
        "expected_season_end_date",
        "rule_version",
        "assessed_at",
    )

    list_filter = (
        "status",
        "rule_version",
        "assessed_at",
    )

    search_fields = (
        "planting_attempt__crop__name",
        "planting_attempt__variety__name",
        "planting_attempt__field__farm__name",
    )

    readonly_fields = (
        "assessed_at",
        "created_at",
    )
