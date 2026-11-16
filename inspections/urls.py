from django.urls import path

from . import views


app_name = "inspections"

urlpatterns = [
    path("", views.inspection_list, name="list"),
    path("add/", views.inspection_create, name="create"),
    path("<int:pk>/", views.inspection_detail, name="detail"),
    path("<int:pk>/edit/", views.inspection_update, name="update"),
    path("<int:pk>/delete/", views.inspection_delete, name="delete"),
]
