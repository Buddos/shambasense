from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from farms.models import Farm
from planting.models import PlantingAttempt
from inspections.models import Inspection
from decision_engine.models import (
    EstablishmentAssessment,
    RemainingSeasonAssessment,
)
from recommendations.models import Recommendation

from .services import get_report_data
from .pdf import build_pdf_response


@login_required
def report_dashboard(request):
    data = get_report_data(request.user)

    return render(request, "reports/dashboard.html", {
        "summary": data["summary"],
        "farms": data["farms"],
        "plantings": data["plantings"],
        "inspections": data["inspections"],
    })


@login_required
def farm_report(request, farm_id):
    farm = get_object_or_404(
        Farm.objects.prefetch_related(
            "fields__planting_attempts__crop",
            "fields__planting_attempts__variety",
        ),
        pk=farm_id,
        owner=request.user,
    )

    return render(request, "reports/farm_detail.html", {
        "farm": farm,
        "fields": farm.fields.all(),
    })


@login_required
def planting_report(request, planting_id):
    planting = get_object_or_404(
        PlantingAttempt.objects.select_related(
            "field",
            "field__farm",
            "crop",
            "variety",
        ),
        pk=planting_id,
        field__farm__owner=request.user,
    )

    inspections = planting.inspections.select_related(
        "inspected_by",
    ).order_by("-inspection_date")

    establishment_assessments = EstablishmentAssessment.objects.filter(
        inspection__planting_attempt=planting,
    ).select_related("inspection").prefetch_related("recommendations")

    season_assessment = RemainingSeasonAssessment.objects.filter(
        planting_attempt=planting,
    ).first()

    return render(request, "reports/planting_detail.html", {
        "planting": planting,
        "inspections": inspections,
        "establishment_assessments": establishment_assessments,
        "season_assessment": season_assessment,
    })


@login_required
def inspection_report(request, inspection_id):
    inspection = get_object_or_404(
        Inspection.objects.select_related(
            "planting_attempt",
            "planting_attempt__field__farm",
            "planting_attempt__crop",
            "planting_attempt__variety",
            "inspected_by",
        ),
        pk=inspection_id,
        planting_attempt__field__farm__owner=request.user,
    )

    assessment = getattr(
        inspection,
        "establishment_assessment",
        None,
    )

    recommendations = (
        assessment.recommendations.all()
        if assessment
        else Recommendation.objects.none()
    )

    return render(request, "reports/inspection_detail.html", {
        "inspection": inspection,
        "assessment": assessment,
        "recommendations": recommendations,
    })


@login_required
def assessment_report(request, planting_id):
    planting = get_object_or_404(
        PlantingAttempt.objects.select_related(
            "field__farm",
            "crop",
            "variety",
        ),
        pk=planting_id,
        field__farm__owner=request.user,
    )

    establishment_assessments = EstablishmentAssessment.objects.filter(
        inspection__planting_attempt=planting,
    ).select_related("inspection").prefetch_related("recommendations")

    season_assessment = RemainingSeasonAssessment.objects.filter(
        planting_attempt=planting,
    ).first()

    return render(request, "reports/assessment_detail.html", {
        "planting": planting,
        "establishment_assessments": establishment_assessments,
        "season_assessment": season_assessment,
    })


@login_required
def recommendation_report(request, recommendation_id):
    recommendation = get_object_or_404(
        Recommendation.objects.select_related(
            "assessment",
            "assessment__inspection",
            "assessment__inspection__planting_attempt",
            "assessment__inspection__planting_attempt__field__farm",
            "assessment__inspection__planting_attempt__crop",
            "assessment__inspection__planting_attempt__variety",
        ),
        pk=recommendation_id,
        assessment__inspection__planting_attempt__field__farm__owner=request.user,
    )

    return render(request, "reports/recommendation_detail.html", {
        "recommendation": recommendation,
    })


# ---------------------------------------------------------
# PDF DOWNLOADS
# ---------------------------------------------------------

@login_required
def farm_report_pdf(request, farm_id):
    farm = get_object_or_404(
        Farm,
        pk=farm_id,
        owner=request.user,
    )

    fields = farm.fields.all()

    sections = [
        ("Farm information", [
            ("Farm", farm.name),
            ("County", farm.county),
            ("Sub-county", farm.sub_county),
            ("Ward", farm.ward),
            ("Village", farm.village),
            ("Total acreage", farm.total_acreage),
            ("Location description", farm.location_description),
            ("Notes", farm.notes),
        ]),
        ("Fields", [
            (
                f"{field.name}",
                f"{field.acreage} acres | Soil: {field.soil_type or 'Not recorded'}",
            )
            for field in fields
        ]),
    ]

    return build_pdf_response(
        f"Farm Report - {farm.name}",
        sections,
        f"farm-report-{farm.pk}.pdf",
    )


@login_required
def planting_report_pdf(request, planting_id):
    planting = get_object_or_404(
        PlantingAttempt.objects.select_related(
            "field__farm",
            "crop",
            "variety",
        ),
        pk=planting_id,
        field__farm__owner=request.user,
    )

    inspections = planting.inspections.order_by("-inspection_date")

    sections = [
        ("Planting information", [
            ("Farm", planting.field.farm.name),
            ("Field", planting.field.name),
            ("Crop", planting.crop.name),
            ("Variety", planting.variety.name),
            ("Planting date", planting.planting_date),
            ("Expected season end", planting.expected_season_end_date),
            ("Area planted (acres)", planting.area_planted),
            ("Planting method", planting.get_planting_method_display()),
            ("Status", planting.get_status_display()),
            ("Seed source", planting.seed_source),
            ("Notes", planting.notes),
        ]),
        ("Inspection history", [
            (
                f"Inspection on {inspection.inspection_date}",
                f"Stage: {inspection.get_crop_stage_display()} | "
                f"Condition: {inspection.get_crop_condition_display()}",
            )
            for inspection in inspections
        ]),
    ]

    return build_pdf_response(
        f"Planting Report - {planting.crop.name}",
        sections,
        f"planting-report-{planting.pk}.pdf",
    )


@login_required
def inspection_report_pdf(request, inspection_id):
    inspection = get_object_or_404(
        Inspection.objects.select_related(
            "planting_attempt__field__farm",
            "planting_attempt__crop",
            "planting_attempt__variety",
            "inspected_by",
        ),
        pk=inspection_id,
        planting_attempt__field__farm__owner=request.user,
    )

    sections = [
        ("Inspection information", [
            ("Farm", inspection.planting_attempt.field.farm.name),
            ("Crop", inspection.planting_attempt.crop.name),
            ("Variety", inspection.planting_attempt.variety.name),
            ("Inspection date", inspection.inspection_date),
            ("Crop stage", inspection.get_crop_stage_display()),
            ("Inspected by", inspection.inspected_by or "Not recorded"),
            ("Crop condition", inspection.get_crop_condition_display()),
            ("Soil moisture", inspection.get_soil_moisture_display()),
            ("Weed pressure", inspection.get_weed_pressure_display()),
            ("Planting stations observed", inspection.planting_stations_observed),
            ("Stations with emergence", inspection.stations_with_emergence),
            ("Emergence percentage", inspection.emergence_percentage),
            ("Healthy plants", inspection.healthy_plant_count),
            ("Damaged plants", inspection.damaged_plant_count),
            ("Pest or disease signs", "Yes" if inspection.pest_or_disease_signs else "No"),
            ("Observations", inspection.observations),
            ("Actions taken", inspection.actions_taken),
            ("Follow-up date", inspection.follow_up_date),
        ]),
    ]

    assessment = getattr(inspection, "establishment_assessment", None)

    if assessment:
        sections.append(("Establishment assessment", [
            ("Status", assessment.get_status_display()),
            ("Summary", assessment.summary),
            ("Emergence percentage", assessment.emergence_percentage),
            ("Rule version", assessment.rule_version),
        ]))

        sections.append(("Recommendations", [
            (
                recommendation.title,
                recommendation.recommended_action,
            )
            for recommendation in assessment.recommendations.all()
        ]))

    return build_pdf_response(
        "Inspection Report",
        sections,
        f"inspection-report-{inspection.pk}.pdf",
    )


@login_required
def assessment_report_pdf(request, planting_id):
    planting = get_object_or_404(
        PlantingAttempt.objects.select_related(
            "field__farm",
            "crop",
            "variety",
        ),
        pk=planting_id,
        field__farm__owner=request.user,
    )

    establishment_assessments = EstablishmentAssessment.objects.filter(
        inspection__planting_attempt=planting,
    ).select_related("inspection")

    season_assessment = RemainingSeasonAssessment.objects.filter(
        planting_attempt=planting,
    ).first()

    sections = [
        ("Planting", [
            ("Farm", planting.field.farm.name),
            ("Field", planting.field.name),
            ("Crop", planting.crop.name),
            ("Variety", planting.variety.name),
            ("Planting date", planting.planting_date),
        ]),
    ]

    for assessment in establishment_assessments:
        sections.append((
            f"Establishment assessment - {assessment.inspection.inspection_date}",
            [
                ("Status", assessment.get_status_display()),
                ("Summary", assessment.summary),
                ("Emergence percentage", assessment.emergence_percentage),
                ("Healthy plants", assessment.healthy_plant_count),
                ("Damaged plants", assessment.damaged_plant_count),
                ("Rule version", assessment.rule_version),
            ],
        ))

    if season_assessment:
        sections.append(("Remaining-season assessment", [
            ("Status", season_assessment.get_status_display()),
            ("Assessment date", season_assessment.assessment_date),
            ("Expected maturity start", season_assessment.expected_maturity_start),
            ("Expected maturity end", season_assessment.expected_maturity_end),
            ("Expected season end", season_assessment.expected_season_end_date),
            ("Days after planting", season_assessment.days_after_planting),
            ("Summary", season_assessment.summary),
            ("Rule version", season_assessment.rule_version),
        ]))

    return build_pdf_response(
        "Assessment Report",
        sections,
        f"assessment-report-{planting.pk}.pdf",
    )


@login_required
def recommendation_report_pdf(request, recommendation_id):
    recommendation = get_object_or_404(
        Recommendation.objects.select_related(
            "assessment__inspection__planting_attempt__field__farm",
            "assessment__inspection__planting_attempt__crop",
            "assessment__inspection__planting_attempt__variety",
        ),
        pk=recommendation_id,
        assessment__inspection__planting_attempt__field__farm__owner=request.user,
    )

    planting = recommendation.assessment.inspection.planting_attempt

    sections = [
        ("Recommendation information", [
            ("Farm", planting.field.farm.name),
            ("Crop", planting.crop.name),
            ("Variety", planting.variety.name),
            ("Title", recommendation.title),
            ("Category", recommendation.get_category_display()),
            ("Priority", recommendation.get_priority_display()),
            ("Status", recommendation.get_status_display()),
            ("Explanation", recommendation.explanation),
            ("Recommended action", recommendation.recommended_action),
            ("Active", "Yes" if recommendation.is_active else "No"),
            ("Follow-up date", recommendation.follow_up_date),
            ("Rule version", recommendation.rule_version),
        ]),
    ]

    return build_pdf_response(
        "Recommendation Report",
        sections,
        f"recommendation-report-{recommendation.pk}.pdf",
    )
