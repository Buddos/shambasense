from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from recommendations.services import generate_recommendations

from decision_engine.services import assess_establishment

from .forms import InspectionForm
from .models import Inspection


def user_inspections(user):
    return (
        Inspection.objects
        .filter(planting_attempt__field__farm__owner=user)
        .select_related(
            "planting_attempt",
            "planting_attempt__field",
            "planting_attempt__field__farm",
            "planting_attempt__crop",
            "planting_attempt__variety",
            "inspected_by",
        )
    )


@login_required
def inspection_list(request):
    inspections = user_inspections(request.user)

    return render(
        request,
        "inspections/inspection_list.html",
        {"inspections": inspections},
    )


@login_required
def inspection_create(request):
    if request.method == "POST":
        form = InspectionForm(request.POST, user=request.user)

        if form.is_valid():
            inspection = form.save(commit=False)
            inspection.inspected_by = request.user
            inspection.full_clean()
            inspection.save()

            # Run the establishment decision engine
            assessment = assess_establishment(inspection)
            generate_recommendations(assessment)

            messages.success(
                request,
                "Field inspection recorded successfully.",
            )

            return redirect(
                "inspections:detail",
                pk=inspection.pk,
            )
    else:
        form = InspectionForm(user=request.user)

    return render(
        request,
        "inspections/inspection_form.html",
        {
            "form": form,
            "title": "Record Field Inspection",
            "submit_text": "Save Inspection",
        },
    )


@login_required
def inspection_detail(request, pk):
    inspection = get_object_or_404(
        user_inspections(request.user),
        pk=pk,
    )

    return render(
        request,
        "inspections/inspection_detail.html",
        {"inspection": inspection},
    )


@login_required
def inspection_update(request, pk):
    inspection = get_object_or_404(
        user_inspections(request.user),
        pk=pk,
    )

    if request.method == "POST":
        form = InspectionForm(
            request.POST,
            instance=inspection,
            user=request.user,
        )

        if form.is_valid():
            updated_inspection = form.save(commit=False)
            updated_inspection.inspected_by = inspection.inspected_by
            updated_inspection.full_clean()
            updated_inspection.save()

            # Re-run the decision engine so the assessment
            # reflects the updated inspection observations.
            assessment = assess_establishment(updated_inspection)
            generate_recommendations(assessment)

            messages.success(
                request,
                "Inspection updated successfully.",
            )

            return redirect(
                "inspections:detail",
                pk=inspection.pk,
            )
    else:
        form = InspectionForm(
            instance=inspection,
            user=request.user,
        )

    return render(
        request,
        "inspections/inspection_form.html",
        {
            "form": form,
            "title": "Update Field Inspection",
            "submit_text": "Update Inspection",
            "inspection": inspection,
        },
    )


@login_required
def inspection_delete(request, pk):
    inspection = get_object_or_404(
        user_inspections(request.user),
        pk=pk,
    )

    if request.method == "POST":
        inspection.delete()

        messages.success(
            request,
            "Inspection deleted successfully.",
        )

        return redirect("inspections:list")

    return render(
        request,
        "inspections/inspection_confirm_delete.html",
        {"inspection": inspection},
    )