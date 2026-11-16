from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from decision_engine.remaining_season import assess_remaining_season

from .forms import PlantingAttemptForm
from .models import PlantingAttempt


def get_user_planting_or_404(user, pk):
    return get_object_or_404(
        PlantingAttempt.objects.select_related(
            "field",
            "field__farm",
            "crop",
            "variety",
        ),
        pk=pk,
        field__farm__owner=user,
    )


@login_required
def planting_list(request):
    plantings = (
        PlantingAttempt.objects
        .filter(field__farm__owner=request.user)
        .select_related(
            "field",
            "field__farm",
            "crop",
            "variety",
        )
    )

    return render(
        request,
        "planting/planting_list.html",
        {"plantings": plantings},
    )


@login_required
def planting_detail(request, pk):
    planting = get_user_planting_or_404(request.user, pk)

    assessment = getattr(
        planting,
        "remaining_season_assessment",
        None,
    )

    return render(
        request,
        "planting/planting_detail.html",
        {
            "planting": planting,
            "remaining_season_assessment": assessment,
        },
    )


@login_required
@require_POST
def planting_assess_remaining_season(request, pk):
    planting = get_user_planting_or_404(request.user, pk)

    assess_remaining_season(planting)

    messages.success(
        request,
        "Remaining-season assessment completed successfully.",
    )

    return redirect("planting:detail", pk=planting.pk)


@login_required
def planting_create(request):
    if request.method == "POST":
        form = PlantingAttemptForm(
            request.POST,
            user=request.user,
        )

        if form.is_valid():
            planting = form.save()

            messages.success(
                request,
                "Planting record created successfully.",
            )

            return redirect("planting:detail", pk=planting.pk)
    else:
        form = PlantingAttemptForm(user=request.user)

    return render(
        request,
        "planting/planting_form.html",
        {
            "form": form,
            "title": "Record Planting",
            "submit_text": "Save Planting Record",
        },
    )


@login_required
def planting_update(request, pk):
    planting = get_user_planting_or_404(request.user, pk)

    if request.method == "POST":
        form = PlantingAttemptForm(
            request.POST,
            instance=planting,
            user=request.user,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Planting record updated successfully.",
            )

            return redirect("planting:detail", pk=planting.pk)
    else:
        form = PlantingAttemptForm(
            instance=planting,
            user=request.user,
        )

    return render(
        request,
        "planting/planting_form.html",
        {
            "form": form,
            "title": "Edit Planting Record",
            "submit_text": "Update Planting Record",
            "planting": planting,
        },
    )


@login_required
def planting_delete(request, pk):
    planting = get_user_planting_or_404(request.user, pk)

    if request.method == "POST":
        planting.delete()

        messages.success(
            request,
            "Planting record deleted successfully.",
        )

        return redirect("planting:list")

    return render(
        request,
        "planting/planting_confirm_delete.html",
        {"planting": planting},
    )
