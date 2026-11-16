
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.FarmerRegistrationView.as_view(), name="register"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("profile/", views.account_profile, name="profile"),
    path("settings/", views.platform_settings, name="settings"),
]
