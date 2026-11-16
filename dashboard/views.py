from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from decision_engine.models import (
    EstablishmentAssessment,
    RemainingSeasonAssessment,
)
from farms.models import Farm, Field
from inspections.models import Inspection
from planting.models import PlantingAttempt
from recommendations.models import Recommendation


@login_required
def dashboard_home(request):
    user = request.user

    farms = Farm.objects.filter(owner=user)
    fields = Field.objects.filter(farm__owner=user)

    plantings = PlantingAttempt.objects.filter(
        field__farm__owner=user
    )

    inspections = Inspection.objects.filter(
        planting_attempt__field__farm__owner=user
    )

    recommendations = Recommendation.objects.filter(
        assessment__inspection__planting_attempt__field__farm__owner=user
    )

    # General farm statistics
    farms_count = farms.count()
    fields_count = fields.count()
    planting_count = plantings.count()
    inspections_count = inspections.count()

    # Planting lifecycle
    active_planting_count = plantings.filter(
        status=PlantingAttempt.Status.ACTIVE
    ).count()

    completed_planting_count = plantings.filter(
        status=PlantingAttempt.Status.COMPLETED
    ).count()

    abandoned_planting_count = plantings.filter(
        status=PlantingAttempt.Status.ABANDONED
    ).count()

    replaced_planting_count = plantings.filter(
        status=PlantingAttempt.Status.REPLACED
    ).count()

    # Outstanding recommendations
    outstanding_recommendations = recommendations.filter(
        is_active=True,
        status__in=[
            Recommendation.Status.PENDING,
            Recommendation.Status.IN_PROGRESS,
        ],
    )

    outstanding_recommendations_count = (
        outstanding_recommendations.count()
    )

    high_priority_recommendations_count = (
        outstanding_recommendations.filter(
            priority=Recommendation.Priority.HIGH
        ).count()
    )

    # Establishment decision alerts
    establishment_assessments = EstablishmentAssessment.objects.filter(
        inspection__planting_attempt__field__farm__owner=user
    )

    establishment_attention_count = (
        establishment_assessments.filter(
            status=EstablishmentAssessment.Status.ATTENTION_REQUIRED
        ).count()
    )

    # Remaining-season decision alerts
    remaining_season_assessments = (
        RemainingSeasonAssessment.objects.filter(
            planting_attempt__field__farm__owner=user
        )
    )

    season_attention_count = remaining_season_assessments.filter(
        status__in=[
            RemainingSeasonAssessment.Status.ATTENTION_REQUIRED,
            RemainingSeasonAssessment.Status.SEASON_CONSTRAINT,
            RemainingSeasonAssessment.Status.MATURITY_WINDOW_ELAPSED,
        ]
    ).count()

    total_attention_count = (
        establishment_attention_count + season_attention_count
    )

    # Latest inspection and its establishment assessment
    latest_inspection = (
        inspections
        .select_related(
            "planting_attempt__crop",
            "planting_attempt__variety",
            "planting_attempt__field__farm",
        )
        .first()
    )

    latest_establishment_assessment = None

    if latest_inspection:
        latest_establishment_assessment = (
            EstablishmentAssessment.objects.filter(
                inspection=latest_inspection
            ).first()
        )

    # Latest remaining-season assessment
    latest_remaining_season_assessment = (
        remaining_season_assessments
        .select_related(
            "planting_attempt__crop",
            "planting_attempt__variety",
            "planting_attempt__field__farm",
        )
        .first()
    )

    # Recent planting activity
    recent_plantings = (
        plantings
        .select_related(
            "crop",
            "variety",
            "field__farm",
        )[:5]
    )

    # Recent inspections
    recent_inspections = (
        inspections
        .select_related(
            "planting_attempt__crop",
            "planting_attempt__variety",
            "planting_attempt__field__farm",
        )[:5]
    )

    # Recent outstanding recommendations
    recent_recommendations = (
        outstanding_recommendations
        .select_related(
            "assessment__inspection__planting_attempt__crop",
            "assessment__inspection__planting_attempt__variety",
            "assessment__inspection__planting_attempt__field__farm",
        )[:5]
    )

    context = {
        "farms_count": farms_count,
        "fields_count": fields_count,
        "planting_count": planting_count,
        "active_planting_count": active_planting_count,
        "completed_planting_count": completed_planting_count,
        "abandoned_planting_count": abandoned_planting_count,
        "replaced_planting_count": replaced_planting_count,
        "inspections_count": inspections_count,
        "outstanding_recommendations_count": (
            outstanding_recommendations_count
        ),
        "high_priority_recommendations_count": (
            high_priority_recommendations_count
        ),
        "establishment_attention_count": establishment_attention_count,
        "season_attention_count": season_attention_count,
        "total_attention_count": total_attention_count,
        "latest_inspection": latest_inspection,
        "latest_establishment_assessment": (
            latest_establishment_assessment
        ),
        "latest_remaining_season_assessment": (
            latest_remaining_season_assessment
        ),
        "recent_plantings": recent_plantings,
        "recent_inspections": recent_inspections,
        "recent_recommendations": recent_recommendations,
    }

    return render(request, "dashboard/home.html", context)
