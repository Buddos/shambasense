from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.report_dashboard, name="dashboard"),

    # HTML reports
    path("farm/<int:farm_id>/", views.farm_report, name="farm_detail"),
    path("planting/<int:planting_id>/", views.planting_report, name="planting_detail"),
    path("inspection/<int:inspection_id>/", views.inspection_report, name="inspection_detail"),
    path("assessments/<int:planting_id>/", views.assessment_report, name="assessment_detail"),
    path("recommendation/<int:recommendation_id>/", views.recommendation_report, name="recommendation_detail"),

    # PDF downloads
    path("pdf/farm/<int:farm_id>/", views.farm_report_pdf, name="farm_pdf"),
    path("pdf/planting/<int:planting_id>/", views.planting_report_pdf, name="planting_pdf"),
    path("pdf/inspection/<int:inspection_id>/", views.inspection_report_pdf, name="inspection_pdf"),
    path("pdf/assessments/<int:planting_id>/", views.assessment_report_pdf, name="assessment_pdf"),
    path("pdf/recommendation/<int:recommendation_id>/", views.recommendation_report_pdf, name="recommendation_pdf"),
]
