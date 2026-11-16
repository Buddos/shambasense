
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("pages.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("accounts/", include("accounts.urls")),
    path("farms/", include("farms.urls")),
    path("crops/", include("crops.urls")),
    path("planting/", include("planting.urls")),
    path("inspections/", include("inspections.urls")),
    path("recommendations/", include("recommendations.urls")),
    path("assessments/", include("decision_engine.urls")),
    path("reports/", include("reports.urls")),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
