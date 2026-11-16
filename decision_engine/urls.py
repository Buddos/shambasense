from django.urls import path

from . import views


app_name = "decision_engine"

urlpatterns = [
    path("", views.assessment_history, name="history"),
    path(
        "establishment/<int:inspection_pk>/",
        views.establishment_detail,
        name="establishment_detail",
    ),
    path(
        "remaining-season/<int:planting_pk>/",
        views.remaining_season_detail,
        name="remaining_season_detail",
    ),
]
