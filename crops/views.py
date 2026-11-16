from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import Crop, Variety


@login_required
def crop_list(request):
    crops = (
        Crop.objects
        .filter(is_active=True)
        .prefetch_related("varieties")
    )

    return render(
        request,
        "crops/crop_list.html",
        {
            "crops": crops,
        },
    )


@login_required
def crop_detail(request, pk):
    crop = get_object_or_404(
        Crop.objects.prefetch_related("varieties"),
        pk=pk,
        is_active=True,
    )

    return render(
        request,
        "crops/crop_detail.html",
        {
            "crop": crop,
        },
    )


@login_required
def variety_detail(request, pk):
    variety = get_object_or_404(
        Variety.objects.select_related("crop"),
        pk=pk,
        is_active=True,
        crop__is_active=True,
    )

    return render(
        request,
        "crops/variety_detail.html",
        {
            "variety": variety,
        },
    )
