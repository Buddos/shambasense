from django.db.models import Count, Q

from farms.models import Farm, Field
from planting.models import PlantingAttempt
from inspections.models import Inspection
from decision_engine.models import (
    EstablishmentAssessment,
    RemainingSeasonAssessment,
)
from recommendations.models import Recommendation


def get_report_data(user):
    """
    Return report data restricted to records owned by the given user.
    """

    farms = Farm.objects.filter(owner=user)

    fields = Field.objects.filter(farm__owner=user)

    plantings = PlantingAttempt.objects.filter(
        field__farm__owner=user
    ).select_related(
        "field",
        "field__farm",
        "crop",
        "variety",
    )

    inspections = Inspection.objects.filter(
        planting_attempt__field__farm__owner=user
    ).select_related(
        "planting_attempt",
        "planting_attempt__field",
        "planting_attempt__field__farm",
        "planting_attempt__crop",
        "planting_attempt__variety",
        "inspected_by",
    )

    establishment_assessments = EstablishmentAssessment.objects.filter(
        inspection__planting_attempt__field__farm__owner=user
    ).select_related(
        "inspection",
        "inspection__planting_attempt",
        "inspection__planting_attempt__field__farm",
        "inspection__planting_attempt__crop",
        "inspection__planting_attempt__variety",
    )

    season_assessments = RemainingSeasonAssessment.objects.filter(
        planting_attempt__field__farm__owner=user
    ).select_related(
        "planting_attempt",
        "planting_attempt__field__farm",
        "planting_attempt__crop",
        "planting_attempt__variety",
        "latest_inspection",
    )

    recommendations = Recommendation.objects.filter(
        assessment__inspection__planting_attempt__field__farm__owner=user
    ).select_related(
        "assessment",
        "assessment__inspection",
        "assessment__inspection__planting_attempt",
        "assessment__inspection__planting_attempt__field__farm",
        "assessment__inspection__planting_attempt__crop",
        "assessment__inspection__planting_attempt__variety",
    )

    return {
        "farms": farms,
        "fields": fields,
        "plantings": plantings,
        "inspections": inspections,
        "establishment_assessments": establishment_assessments,
        "season_assessments": season_assessments,
        "recommendations": recommendations,
        "summary": {
            "farm_count": farms.count(),
            "field_count": fields.count(),
            "planting_count": plantings.count(),
            "inspection_count": inspections.count(),
            "establishment_count": establishment_assessments.count(),
            "season_assessment_count": season_assessments.count(),
            "active_recommendation_count": recommendations.filter(
                is_active=True,
            ).exclude(
                status__in=[
                    Recommendation.Status.COMPLETED,
                    Recommendation.Status.DISMISSED,
                ]
            ).count(),
            "high_priority_count": recommendations.filter(
                is_active=True,
                priority=Recommendation.Priority.HIGH,
            ).exclude(
                status__in=[
                    Recommendation.Status.COMPLETED,
                    Recommendation.Status.DISMISSED,
                ]
            ).count(),
        },
    }
