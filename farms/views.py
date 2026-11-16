from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from .forms import FarmForm, FieldForm
from .models import Farm, Field


@login_required
def farm_list(request):
    farms = (
        Farm.objects
        .filter(owner=request.user)
        .annotate(field_count=Count("fields"))
    )

    return render(
        request,
        "farms/farm_list.html",
        {"farms": farms},
    )


@login_required
def farm_create(request):
    if request.method == "POST":
        form = FarmForm(request.POST)

        if form.is_valid():
            farm = form.save(commit=False)
            farm.owner = request.user
            farm.save()

            messages.success(
                request,
                f"Farm '{farm.name}' was successfully added.",
            )

            return redirect("farms:detail", pk=farm.pk)
    else:
        form = FarmForm()

    return render(
        request,
        "farms/farm_form.html",
        {
            "form": form,
            "page_title": "Add Farm",
        },
    )


@login_required
def farm_detail(request, pk):
    farm = get_object_or_404(
        Farm.objects.prefetch_related("fields"),
        pk=pk,
        owner=request.user,
    )

    return render(
        request,
        "farms/farm_detail.html",
        {"farm": farm},
    )


@login_required
def farm_update(request, pk):
    farm = get_object_or_404(
        Farm,
        pk=pk,
        owner=request.user,
    )

    if request.method == "POST":
        form = FarmForm(request.POST, instance=farm)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                f"Farm '{farm.name}' was updated successfully.",
            )

            return redirect("farms:detail", pk=farm.pk)
    else:
        form = FarmForm(instance=farm)

    return render(
        request,
        "farms/farm_form.html",
        {
            "form": form,
            "farm": farm,
            "page_title": "Edit Farm",
        },
    )


@login_required
def farm_delete(request, pk):
    farm = get_object_or_404(
        Farm,
        pk=pk,
        owner=request.user,
    )

    if request.method == "POST":
        farm_name = farm.name
        farm.delete()

        messages.success(
            request,
            f"Farm '{farm_name}' was deleted.",
        )

        return redirect("farms:list")

    return render(
        request,
        "farms/farm_confirm_delete.html",
        {"farm": farm},
    )


@login_required
def field_create(request, farm_pk):
    farm = get_object_or_404(
        Farm,
        pk=farm_pk,
        owner=request.user,
    )

    if request.method == "POST":
        form = FieldForm(request.POST)

        if form.is_valid():
            field = form.save(commit=False)
            field.farm = farm
            field.save()

            messages.success(
                request,
                f"Field '{field.name}' was added to {farm.name}.",
            )

            return redirect("farms:detail", pk=farm.pk)
    else:
        form = FieldForm()

    return render(
        request,
        "farms/field_form.html",
        {
            "form": form,
            "farm": farm,
            "page_title": "Add Field",
        },
    )


@login_required
def field_update(request, pk):
    field = get_object_or_404(
        Field.objects.select_related("farm"),
        pk=pk,
        farm__owner=request.user,
    )

    if request.method == "POST":
        form = FieldForm(request.POST, instance=field)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                f"Field '{field.name}' was updated successfully.",
            )

            return redirect("farms:detail", pk=field.farm.pk)
    else:
        form = FieldForm(instance=field)

    return render(
        request,
        "farms/field_form.html",
        {
            "form": form,
            "farm": field.farm,
            "field": field,
            "page_title": "Edit Field",
        },
    )


@login_required
def field_delete(request, pk):
    field = get_object_or_404(
        Field.objects.select_related("farm"),
        pk=pk,
        farm__owner=request.user,
    )

    farm = field.farm

    if request.method == "POST":
        field_name = field.name
        field.delete()

        messages.success(
            request,
            f"Field '{field_name}' was deleted.",
        )

        return redirect("farms:detail", pk=farm.pk)

    return render(
        request,
        "farms/field_confirm_delete.html",
        {"field": field},
    )