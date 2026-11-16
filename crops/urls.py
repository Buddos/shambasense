from django.urls import path

from . import views

app_name = "crops"

urlpatterns = [
    path("", views.crop_list, name="list"),
    path("<int:pk>/", views.crop_detail, name="detail"),
    path(
        "varieties/<int:pk>/",
        views.variety_detail,
        name="variety_detail",
    ),
]
