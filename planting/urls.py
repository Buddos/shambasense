from django.urls import path

from . import views


app_name = "planting"


urlpatterns = [
    path("", views.planting_list, name="list"),
    path("add/", views.planting_create, name="create"),
    path(
        "<int:pk>/assess-remaining-season/",
        views.planting_assess_remaining_season,
        name="assess_remaining_season",
    ),
    path("<int:pk>/", views.planting_detail, name="detail"),
    path("<int:pk>/edit/", views.planting_update, name="update"),
    path("<int:pk>/delete/", views.planting_delete, name="delete"),
]
