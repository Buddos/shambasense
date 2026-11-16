from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Case, IntegerField, Q, Value, When
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import RecommendationUpdateForm
from .models import Recommendation


def user_recommendations(user):
    """
    Return recommendations belonging to planting attempts
    on farms owned by the currently logged-in user.
    """
    return (
        Recommendation.objects
        .filter(
            Q(
                assessment__inspection__planting_attempt__field__farm__owner=user
            )
            | Q(
                remaining_season_assessment__planting_attempt__field__farm__owner=user
            )
        )
        .select_related(
            "assessment",
            "assessment__inspection",
            "assessment__inspection__planting_attempt",
            "assessment__inspection__planting_attempt__crop",
            "assessment__inspection__planting_attempt__variety",
            "assessment__inspection__planting_attempt__field",
            "assessment__inspection__planting_attempt__field__farm",
            "remaining_season_assessment",
            "remaining_season_assessment__latest_inspection",
            "remaining_season_assessment__planting_attempt",
            "remaining_season_assessment__planting_attempt__crop",
            "remaining_season_assessment__planting_attempt__variety",
            "remaining_season_assessment__planting_attempt__field",
            "remaining_season_assessment__planting_attempt__field__farm",
        )
        .annotate(
            priority_order=Case(
                When(priority=Recommendation.Priority.HIGH, then=Value(0)),
                When(priority=Recommendation.Priority.MEDIUM, then=Value(1)),
                When(priority=Recommendation.Priority.LOW, then=Value(2)),
                When(
                    priority=Recommendation.Priority.INFORMATIONAL,
                    then=Value(3),
                ),
                default=Value(4),
                output_field=IntegerField(),
            )
        )
        .order_by("priority_order", "-created_at")
    )


@login_required
def recommendation_list(request):
    active_recommendations = user_recommendations(request.user).filter(
        is_active=True,
    )
    is_history = request.GET.get("view") == "history"
    recommendations = user_recommendations(request.user).filter(
        is_active=not is_history,
    )

    # Validate filter values against the model's available choices.
    valid_statuses = dict(Recommendation.Status.choices)
    valid_priorities = dict(Recommendation.Priority.choices)
    valid_categories = dict(Recommendation.Category.choices)

    selected_status = request.GET.get("status", "")
    selected_priority = request.GET.get("priority", "")
    selected_category = request.GET.get("category", "")
    search_query = request.GET.get("q", "").strip()

    if selected_status in valid_statuses:
        recommendations = recommendations.filter(status=selected_status)
    else:
        selected_status = ""

    if selected_priority in valid_priorities:
        recommendations = recommendations.filter(priority=selected_priority)
    else:
        selected_priority = ""

    if selected_category in valid_categories:
        recommendations = recommendations.filter(category=selected_category)
    else:
        selected_category = ""

    if search_query:
        recommendations = recommendations.filter(
            Q(title__icontains=search_query)
            | Q(explanation__icontains=search_query)
            | Q(recommended_action__icontains=search_query)
            | Q(assessment__inspection__planting_attempt__crop__name__icontains=search_query)
            | Q(assessment__inspection__planting_attempt__variety__name__icontains=search_query)
            | Q(assessment__inspection__planting_attempt__field__name__icontains=search_query)
            | Q(assessment__inspection__planting_attempt__field__farm__name__icontains=search_query)
            | Q(remaining_season_assessment__planting_attempt__crop__name__icontains=search_query)
            | Q(remaining_season_assessment__planting_attempt__variety__name__icontains=search_query)
            | Q(remaining_season_assessment__planting_attempt__field__name__icontains=search_query)
            | Q(remaining_season_assessment__planting_attempt__field__farm__name__icontains=search_query)
        )

    context = {
        "recommendations": recommendations,
        "is_history": is_history,
        "result_count": recommendations.count(),
        "current_count": active_recommendations.count(),
        "history_count": user_recommendations(request.user).filter(
            is_active=False,
        ).count(),
        "pending_count": active_recommendations.filter(
            status=Recommendation.Status.PENDING
        ).count(),
        "in_progress_count": active_recommendations.filter(
            status=Recommendation.Status.IN_PROGRESS
        ).count(),
        "completed_count": active_recommendations.filter(
            status=Recommendation.Status.COMPLETED
        ).count(),
        "selected_status": selected_status,
        "selected_priority": selected_priority,
        "selected_category": selected_category,
        "search_query": search_query,
        "status_choices": Recommendation.Status.choices,
        "priority_choices": Recommendation.Priority.choices,
        "category_choices": Recommendation.Category.choices,
    }

    return render(
        request,
        "recommendations/recommendation_list.html",
        context,
    )


@login_required
def recommendation_detail(request, pk):
    recommendation = get_object_or_404(
        user_recommendations(request.user),
        pk=pk,
    )

    return render(
        request,
        "recommendations/recommendation_detail.html",
        {"recommendation": recommendation},
    )


@login_required
def recommendation_update(request, pk):
    recommendation = get_object_or_404(
        user_recommendations(request.user).filter(is_active=True),
        pk=pk,
    )

    if request.method == "POST":
        form = RecommendationUpdateForm(
            request.POST,
            instance=recommendation,
        )

        if form.is_valid():
            updated_recommendation = form.save(commit=False)

            if updated_recommendation.status == Recommendation.Status.COMPLETED:
                if not updated_recommendation.completed_at:
                    updated_recommendation.completed_at = timezone.now()
            else:
                updated_recommendation.completed_at = None

            updated_recommendation.save()

            messages.success(
                request,
                "Recommendation progress updated successfully.",
            )
            return redirect(
                "recommendations:detail",
                pk=updated_recommendation.pk,
            )
    else:
        form = RecommendationUpdateForm(instance=recommendation)

    return render(
        request,
        "recommendations/recommendation_update.html",
        {
            "recommendation": recommendation,
            "form": form,
        },
    )
