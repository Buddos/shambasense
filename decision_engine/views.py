from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import EstablishmentAssessment, RemainingSeasonAssessment


def user_establishment_assessments(user):
    return (
        EstablishmentAssessment.objects
        .filter(inspection__planting_attempt__field__farm__owner=user)
        .select_related(
            "inspection",
            "inspection__planting_attempt",
            "inspection__planting_attempt__crop",
            "inspection__planting_attempt__variety",
            "inspection__planting_attempt__field",
            "inspection__planting_attempt__field__farm",
        )
        .prefetch_related("recommendations")
    )


def user_remaining_season_assessments(user):
    return (
        RemainingSeasonAssessment.objects
        .filter(planting_attempt__field__farm__owner=user)
        .select_related(
            "planting_attempt",
            "planting_attempt__crop",
            "planting_attempt__variety",
            "planting_attempt__field",
            "planting_attempt__field__farm",
            "latest_inspection",
        )
    )


@login_required
def assessment_history(request):
    establishment_assessments = user_establishment_assessments(
        request.user
    )
    season_assessments = user_remaining_season_assessments(
        request.user
    )

    context = {
        "establishment_assessments": establishment_assessments,
        "season_assessments": season_assessments,
        "establishment_count": establishment_assessments.count(),
        "season_count": season_assessments.count(),
    }

    return render(
        request,
        "assessments/history.html",
        context,
    )


@login_required
def establishment_detail(request, inspection_pk):
    assessment = get_object_or_404(
        user_establishment_assessments(request.user),
        inspection_id=inspection_pk,
    )

    recommendations = (
        assessment.recommendations
        .all()
        .order_by("-is_active", "-created_at")
    )

    return render(
        request,
        "assessments/establishment_detail.html",
        {
            "assessment": assessment,
            "inspection": assessment.inspection,
            "planting": assessment.inspection.planting_attempt,
            "recommendations": recommendations,
        },
    )


@login_required
def remaining_season_detail(request, planting_pk):
    assessment = get_object_or_404(
        user_remaining_season_assessments(request.user),
        planting_attempt_id=planting_pk,
    )

    return render(
        request,
        "assessments/remaining_season_detail.html",
        {
            "assessment": assessment,
            "planting": assessment.planting_attempt,
        },
    )
