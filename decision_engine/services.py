from decimal import Decimal

from .models import EstablishmentAssessment
from recommendations.services import generate_recommendations


def assess_establishment(inspection):
    """
    Evaluate recorded inspection observations.

    This first version identifies warning indicators.
    It does not use universal crop emergence thresholds
    or make yield predictions.

    After the assessment is created or refreshed, its findings
    are used to generate or refresh farmer recommendations.
    """

    findings = []

    attention_indicators = 0
    monitoring_indicators = 0

    # 1. Emergence sampling
    emergence_percentage = inspection.emergence_percentage

    if emergence_percentage is None:
        findings.append({
            "code": "emergence_data_missing",
            "level": "information",
            "message": (
                "No planting stations were recorded as sampled. "
                "Emergence percentage could not be calculated."
            ),
        })

    else:
        findings.append({
            "code": "emergence_recorded",
            "level": "information",
            "message": (
                f"Emergence was recorded at "
                f"{emergence_percentage}% of sampled stations."
            ),
        })

    # 2. Crop condition
    if inspection.crop_condition == "poor":
        attention_indicators += 1

        findings.append({
            "code": "poor_crop_condition",
            "level": "attention",
            "message": (
                "Poor crop condition was reported. "
                "Investigate the possible causes."
            ),
        })

    elif inspection.crop_condition == "fair":
        monitoring_indicators += 1

        findings.append({
            "code": "fair_crop_condition",
            "level": "monitor",
            "message": (
                "Fair crop condition was reported. "
                "Monitor crop development."
            ),
        })

    # 3. Soil moisture
    if inspection.soil_moisture in ("dry", "waterlogged"):
        attention_indicators += 1

        moisture_messages = {
            "dry": (
                "Dry soil conditions were reported. "
                "Check soil moisture and crop water needs."
            ),
            "waterlogged": (
                "Waterlogged soil conditions were reported. "
                "Investigate drainage and possible root stress."
            ),
        }

        findings.append({
            "code": f"soil_{inspection.soil_moisture}",
            "level": "attention",
            "message": moisture_messages[
                inspection.soil_moisture
            ],
        })

    elif inspection.soil_moisture in ("low", "wet"):
        monitoring_indicators += 1

        findings.append({
            "code": f"soil_{inspection.soil_moisture}",
            "level": "monitor",
            "message": (
                f"Soil moisture was recorded as "
                f"{inspection.get_soil_moisture_display().lower()}. "
                "Continue monitoring field conditions."
            ),
        })

    # 4. Weed pressure
    if inspection.weed_pressure == "high":
        attention_indicators += 1

        findings.append({
            "code": "high_weed_pressure",
            "level": "attention",
            "message": (
                "High weed pressure was reported. "
                "Assess whether weeds are competing with the crop."
            ),
        })

    elif inspection.weed_pressure == "moderate":
        monitoring_indicators += 1

        findings.append({
            "code": "moderate_weed_pressure",
            "level": "monitor",
            "message": (
                "Moderate weed pressure was reported. "
                "Monitor weed competition."
            ),
        })

    # 5. Visible pest or disease signs
    if inspection.pest_or_disease_signs:
        attention_indicators += 1

        findings.append({
            "code": "pest_or_disease_signs",
            "level": "attention",
            "message": (
                "Visible pest or disease signs were reported. "
                "Further field investigation is recommended."
            ),
        })

    # 6. Plant damage
    healthy = inspection.healthy_plant_count
    damaged = inspection.damaged_plant_count

    if damaged > healthy and damaged > 0:
        attention_indicators += 1

        findings.append({
            "code": "damaged_plants_exceed_healthy",
            "level": "attention",
            "message": (
                "The recorded damaged plant count exceeds "
                "the healthy plant count."
            ),
        })

    elif damaged > 0:
        monitoring_indicators += 1

        findings.append({
            "code": "damaged_plants_recorded",
            "level": "monitor",
            "message": (
                f"{damaged} damaged plants were recorded. "
                "Monitor their condition and investigate the cause."
            ),
        })

    else:
        findings.append({
            "code": "no_damaged_plants_recorded",
            "level": "information",
            "message": "No damaged plants were recorded in the sample.",
        })

    # 7. Determine assessment outcome
    if attention_indicators > 0:
        status = EstablishmentAssessment.Status.ATTENTION_REQUIRED

        summary = (
            "One or more significant warning indicators were recorded. "
            "Review the findings and investigate the affected field."
        )

    elif monitoring_indicators > 0:
        status = EstablishmentAssessment.Status.MIXED_SIGNALS

        summary = (
            "Some observations require monitoring. "
            "Continue inspecting the crop and record follow-up findings."
        )

    elif emergence_percentage is None:
        status = EstablishmentAssessment.Status.LIMITED_DATA

        summary = (
            "The available observations do not include emergence "
            "sampling. Record sampled planting stations during "
            "the next inspection."
        )

    else:
        status = EstablishmentAssessment.Status.NO_MAJOR_WARNING_SIGNS

        summary = (
            "No major warning indicators were identified in the "
            "recorded observations. This does not guarantee successful "
            "establishment; continue routine field monitoring."
        )

    # 8. Save or refresh the assessment
    assessment, created = EstablishmentAssessment.objects.update_or_create(
        inspection=inspection,
        defaults={
            "status": status,
            "emergence_percentage": (
                Decimal(str(emergence_percentage))
                if emergence_percentage is not None
                else None
            ),
            "healthy_plant_count": healthy,
            "damaged_plant_count": damaged,
            "findings": findings,
            "summary": summary,
            "rule_version": "1.0",
        },
    )

    # 9. Generate or refresh recommendations from the assessment.
    # Existing recommendation status and follow-up fields are preserved
    # by the recommendation service.
    generate_recommendations(assessment)

    return assessment
