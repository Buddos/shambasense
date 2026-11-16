from django.contrib import admin

from .models import Recommendation


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "priority",
        "status",
        "assessment",
        "created_at",
    )

    list_filter = (
        "category",
        "priority",
        "status",
    )

    search_fields = (
        "title",
        "code",
        "explanation",
        "recommended_action",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "completed_at",
    )