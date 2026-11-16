from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from recommendations.services import generate_remaining_season_recommendations

from .models import (
    EstablishmentAssessment,
    RemainingSeasonAssessment,
)


RULE_VERSION = "1.0"


def assess_remaining_season(planting_attempt, assessment_date=None):
    """
    Assess the recorded maturity window against the expected season end.

    This service does not predict weather, yield, or actual harvest dates.
    Variety maturity days are treated as the recorded expected range.
    """

    assessment_date = assessment_date or timezone.localdate()

    variety = planting_attempt.variety
    planting_date = planting_attempt.planting_date
    season_end = planting_attempt.expected_season_end_date

    maturity_start = (
        planting_date + timedelta(days=variety.maturity_days_min)
        if variety.maturity_days_min
        else None
    )

    maturity_end = (
        planting_date + timedelta(days=variety.maturity_days_max)
        if variety.maturity_days_max
        else None
    )

    elapsed_days = (assessment_date - planting_date).days

    latest_inspection = (
        planting_attempt.inspections
        .select_related("planting_attempt")
        .order_by("-inspection_date", "-created_at")
        .first()
    )

    establishment_status = None
    if latest_inspection:
        try:
            establishment_status = (
                latest_inspection.establishment_assessment.status
            )
        except EstablishmentAssessment.DoesNotExist:
            pass

    evidence = {
        "planting_date": planting_date.isoformat(),
        "variety": variety.name,
        "crop": planting_attempt.crop.name,
        "maturity_days_min": variety.maturity_days_min,
        "maturity_days_max": variety.maturity_days_max,
        "latest_inspection_id": (
            latest_inspection.pk if latest_inspection else None
        ),
        "latest_inspection_date": (
            latest_inspection.inspection_date.isoformat()
            if latest_inspection else None
        ),
        "latest_crop_stage": (
            latest_inspection.crop_stage
            if latest_inspection else None
        ),
        "establishment_status": establishment_status,
    }

    if latest_inspection:
        evidence.update({
            "crop_condition": latest_inspection.crop_condition,
            "soil_moisture": latest_inspection.soil_moisture,
            "weed_pressure": latest_inspection.weed_pressure,
            "pest_or_disease_signs": (
                latest_inspection.pest_or_disease_signs
            ),
            "healthy_plant_count": (
                latest_inspection.healthy_plant_count
            ),
            "damaged_plant_count": (
                latest_inspection.damaged_plant_count
            ),
        })

    # Significant establishment warnings take priority.
    if (
        establishment_status
        == EstablishmentAssessment.Status.ATTENTION_REQUIRED
    ):
        status = RemainingSeasonAssessment.Status.ATTENTION_REQUIRED
        summary = (
            "The latest establishment assessment contains warning "
            "indicators. Investigate these findings before relying on "
            "the maturity timeline."
        )

    elif (
        latest_inspection
        and latest_inspection.crop_stage == "maturity"
    ):
        status = RemainingSeasonAssessment.Status.MATURITY_REACHED
        summary = (
            "The latest inspection records the crop at maturity. "
            "Verify field readiness and crop condition before harvesting."
        )

    elif not planting_date or not maturity_start or not maturity_end:
        status = RemainingSeasonAssessment.Status.INSUFFICIENT_DATA
        summary = (
            "The planting date or variety maturity information is missing. "
            "Complete the planting and variety records before assessing "
            "the maturity timeline."
        )

    elif not season_end:
        status = RemainingSeasonAssessment.Status.INSUFFICIENT_DATA
        summary = (
            "The variety maturity window can be estimated, but no expected "
            "season-end date has been recorded. Add that date to assess "
            "whether the maturity window fits the season."
        )

    elif assessment_date > maturity_end:
        status = (
            RemainingSeasonAssessment.Status.MATURITY_WINDOW_ELAPSED
        )
        summary = (
            "The recorded expected maturity window has elapsed, but the "
            "latest inspection does not record maturity. Reinspect the "
            "crop and seek agronomic advice where necessary."
        )

    elif season_end < maturity_start:
        status = RemainingSeasonAssessment.Status.SEASON_CONSTRAINT
        summary = (
            "The recorded season-end date is earlier than the start of "
            "the variety's expected maturity window. This is a timing "
            "constraint to review with a local agronomist."
        )

    elif season_end >= maturity_end:
        status = (
            RemainingSeasonAssessment.Status.WITHIN_MATURITY_WINDOW
        )
        summary = (
            "The recorded season-end date is on or after the end of the "
            "variety's expected maturity window. The dates are compatible, "
            "but this does not guarantee successful maturity or harvest."
        )

    else:
        status = RemainingSeasonAssessment.Status.TIMING_UNCERTAIN
        summary = (
            "The recorded season-end date falls within the variety's "
            "expected maturity range. Actual timing is uncertain; continue "
            "field monitoring and seek local agronomic guidance."
        )

    with transaction.atomic():
        assessment, created = (
            RemainingSeasonAssessment.objects.update_or_create(
                planting_attempt=planting_attempt,
                defaults={
                    "latest_inspection": latest_inspection,
                    "status": status,
                    "assessment_date": assessment_date,
                    "expected_maturity_start": maturity_start,
                    "expected_maturity_end": maturity_end,
                    "expected_season_end_date": season_end,
                    "days_after_planting": max(elapsed_days, 0),
                    "summary": summary,
                    "evidence": evidence,
                    "rule_version": RULE_VERSION,
                },
            )
        )

    generate_remaining_season_recommendations(assessment)
    return assessment
