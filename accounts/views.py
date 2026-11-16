from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView

from .forms import FarmerRegistrationForm


class FarmerRegistrationView(CreateView):
    form_class = FarmerRegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("accounts:profile")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)

        messages.success(
            self.request,
            "Your ShambaSense account has been created. You can now sign in."
        )

        return response


class UserLoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(
            self.request,
            "Welcome back to ShambaSense."
        )
        return super().form_valid(form)


class UserLogoutView(auth_views.LogoutView):
    next_page = reverse_lazy("accounts:login")


@login_required
def account_profile(request):
    return render(
        request,
        "accounts/profile.html",
        {"account": request.user},
    )


@login_required
def platform_settings(request):
    return render(
        request,
        "accounts/settings.html",
        {
            "platform_settings": {
                "language": settings.LANGUAGE_CODE,
                "time_zone": settings.TIME_ZONE,
                "internationalization": settings.USE_I18N,
                "time_zone_support": settings.USE_TZ,
                "current_time": timezone.localtime(),
                "area_unit": "Acres",
            },
        },
    )