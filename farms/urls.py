from django.urls import path

from . import views

app_name = "farms"

urlpatterns = [
    path("", views.farm_list, name="list"),
    path("add/", views.farm_create, name="create"),
    path("<int:pk>/", views.farm_detail, name="detail"),
    path("<int:pk>/edit/", views.farm_update, name="update"),
    path("<int:pk>/delete/", views.farm_delete, name="delete"),

    path(
        "<int:farm_pk>/fields/add/",
        views.field_create,
        name="field_create",
    ),
    path(
        "fields/<int:pk>/edit/",
        views.field_update,
        name="field_update",
    ),
    path(
        "fields/<int:pk>/delete/",
        views.field_delete,
        name="field_delete",
    ),
]
