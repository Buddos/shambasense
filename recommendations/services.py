from django.db import transaction
from django.db.models import Max

from .models import Recommendation


RULE_VERSION = "1.0"


RECOMMENDATION_RULES = {
    "emergence_data_missing": {
        "code": "emergence_sampling",
        "category": Recommendation.Category.SAMPLING,
        "title": "Record crop emergence during the next inspection",
        "priority": Recommendation.Priority.LOW,
        "action": (
            "During the next field inspection, select representative "
            "planting stations, record the number inspected and the "
            "number with emergence, and use a consistent sampling method."
        ),
    },
    "poor_crop_condition": {
        "code": "poor_crop_condition",
        "category": Recommendation.Category.CROP_HEALTH,
        "title": "Investigate poor crop condition",
        "priority": Recommendation.Priority.HIGH,
        "action": (
            "Inspect affected and apparently healthy areas separately. "
            "Record the distribution of symptoms and check crop stage, "
            "soil conditions, weeds, and visible damage. Seek advice "
            "from a qualified agricultural extension officer where needed."
        ),
    },
    "fair_crop_condition": {
        "code": "fair_crop_condition",
        "category": Recommendation.Category.CROP_HEALTH,
        "title": "Monitor crop development",
        "priority": Recommendation.Priority.MEDIUM,
        "action": (
            "Revisit representative parts of the field and record "
            "changes in crop condition, plant development, and any "
            "new signs of stress."
        ),
    },
    "soil_dry": {
        "code": "soil_dry",
        "category": Recommendation.Category.WATER,
        "title": "Investigate dry soil conditions",
        "priority": Recommendation.Priority.HIGH,
        "action": (
            "Check soil moisture at several representative locations "
            "and assess the crop's water needs. Where water is available "
            "and appropriate for the crop and growth stage, consider "
            "supplementary irrigation."
        ),
    },
    "soil_waterlogged": {
        "code": "soil_waterlogged",
        "category": Recommendation.Category.WATER,
        "title": "Investigate waterlogged areas",
        "priority": Recommendation.Priority.HIGH,
        "action": (
            "Identify affected areas, inspect drainage and soil "
            "conditions, and avoid unnecessary movement of machinery "
            "or people on saturated soil. Seek local agronomic advice "
            "if crop damage is suspected."
        ),
    },
    "soil_low": {
        "code": "soil_low",
        "category": Recommendation.Category.WATER,
        "title": "Continue monitoring soil moisture",
        "priority": Recommendation.Priority.MEDIUM,
        "action": (
            "Check soil moisture again at consistent sampling points. "
            "Record any changes and compare them with crop condition "
            "before deciding whether intervention is needed."
        ),
    },
    "soil_wet": {
        "code": "soil_wet",
        "category": Recommendation.Category.WATER,
        "title": "Monitor wet soil conditions",
        "priority": Recommendation.Priority.LOW,
        "action": (
            "Continue checking soil moisture and observe whether "
            "the soil remains excessively wet. Record any changes "
            "in crop condition or drainage."
        ),
    },
    "high_weed_pressure": {
        "code": "high_weed_pressure",
        "category": Recommendation.Category.WEEDS,
        "title": "Assess and manage high weed pressure",
        "priority": Recommendation.Priority.HIGH,
        "action": (
            "Inspect the distribution and types of weeds and assess "
            "competition with the crop. Plan a control method suitable "
            "for the crop stage and local conditions, following "
            "approved agricultural guidance."
        ),
    },
    "moderate_weed_pressure": {
        "code": "moderate_weed_pressure",
        "category": Recommendation.Category.WEEDS,
        "title": "Monitor and plan weed control",
        "priority": Recommendation.Priority.MEDIUM,
        "action": (
            "Monitor weed growth and crop competition. Plan timely "
            "weed management using methods appropriate to the crop "
            "and local agricultural guidance."
        ),
    },
    "pest_or_disease_signs": {
        "code": "pest_or_disease_investigation",
        "category": Recommendation.Category.PEST_DISEASE,
        "title": "Investigate visible pest or disease signs",
        "priority": Recommendation.Priority.HIGH,
        "action": (
            "Record the affected area, photograph visible symptoms "
            "where possible, and inspect nearby plants. Seek confirmation "
            "from a qualified agricultural extension officer before "
            "choosing any treatment."
        ),
    },
    "damaged_plants_exceed_healthy": {
        "code": "high_plant_damage",
        "category": Recommendation.Category.CROP_HEALTH,
        "title": "Investigate widespread plant damage",
        "priority": Recommendation.Priority.HIGH,
        "action": (
            "Recheck representative plants and record the distribution "
            "and appearance of damaged plants. Investigate possible "
            "causes and seek qualified advice before taking corrective "
            "action."
        ),
    },
    "damaged_plants_recorded": {
        "code": "plant_damage_monitoring",
        "category": Recommendation.Category.CROP_HEALTH,
        "title": "Monitor recorded plant damage",
        "priority": Recommendation.Priority.MEDIUM,
        "action": (
            "Revisit the affected plants during the next inspection. "
            "Record whether damage is increasing, stable, or improving "
            "and document any visible changes."
        ),
    },
}


def _build_evidence(assessment, finding):
    """
    Store the observation that triggered a recommendation.
    Values are kept JSON serializable.
    """
    inspection = assessment.inspection

    return {
        **_build_assessment_evidence(assessment),
        "finding_code": finding.get("code"),
        "finding_level": finding.get("level"),
        "finding_message": finding.get("message"),
        "inspection_date": inspection.inspection_date.isoformat(),
        "crop_condition": inspection.crop_condition,
        "soil_moisture": inspection.soil_moisture,
        "weed_pressure": inspection.weed_pressure,
        "pest_or_disease_signs": inspection.pest_or_disease_signs,
    }


def _build_assessment_evidence(assessment):
    inspection = assessment.inspection
    return {
        "inspection_id": inspection.pk,
        "crop_stage": inspection.crop_stage,
        "planting_stations_observed": inspection.planting_stations_observed,
        "stations_with_emergence": inspection.stations_with_emergence,
        "healthy_plant_count": inspection.healthy_plant_count,
        "damaged_plant_count": inspection.damaged_plant_count,
        "emergence_percentage": (
            str(assessment.emergence_percentage)
            if assessment.emergence_percentage is not None
            else None
        ),
    }


def _sync_recommendations(assessment, source_field, recommendation_specs):
    generated = {}
    source_filter = {source_field: assessment}

    for code, defaults in recommendation_specs.items():
        matching = Recommendation.objects.filter(**source_filter, code=code)
        active = matching.filter(is_active=True).order_by("-occurrence").first()

        if active:
            for field, value in defaults.items():
                setattr(active, field, value)
            active.save()
            recommendation = active
        else:
            last_occurrence = matching.aggregate(
                latest=Max("occurrence"),
            )["latest"] or 0
            recommendation = Recommendation.objects.create(
                **source_filter,
                code=code,
                occurrence=last_occurrence + 1,
                **defaults,
            )

        generated[code] = recommendation

    Recommendation.objects.filter(
        **source_filter,
        is_active=True,
    ).exclude(
        code__in=list(generated),
    ).update(
        is_active=False,
    )

    return list(generated.values())


@transaction.atomic
def generate_recommendations(assessment):
    """
    Generate or refresh recommendations from an establishment
    assessment.

    Existing active recommendation statuses and farmer-entered follow-up
    dates are preserved when recommendation content is refreshed. A
    finding that returns after deactivation starts a new occurrence.

    Recommendations that no longer match current findings are
    deactivated rather than deleted, preserving their history.
    """

    recommendation_specs = {}
    unmapped_findings = []
    findings = assessment.findings or []

    for finding in findings:
        if not isinstance(finding, dict):
            continue

        finding_code = finding.get("code")
        rule = RECOMMENDATION_RULES.get(finding_code)

        if not rule:
            if finding.get("level") in {"attention", "monitor"}:
                unmapped_findings.append(finding)
            continue

        recommendation_code = rule["code"]

        recommendation_specs[recommendation_code] = {
            "category": rule["category"],
            "title": rule["title"],
            "explanation": finding.get(
                "message",
                "This action was generated from the field assessment.",
            ),
            "recommended_action": rule["action"],
            "priority": rule["priority"],
            "evidence": _build_evidence(assessment, finding),
            "rule_version": RULE_VERSION,
            "is_active": True,
        }

    unknown_attention = [
        finding for finding in unmapped_findings
        if finding.get("level") == "attention"
    ]
    unknown_monitoring = [
        finding for finding in unmapped_findings
        if finding.get("level") == "monitor"
    ]

    if unknown_attention or (
        not recommendation_specs
        and assessment.status == "attention_required"
    ):
        messages = [
            finding.get("message")
            for finding in unknown_attention
            if finding.get("message")
        ]
        recommendation_specs["unmapped_attention_review"] = {
            "category": Recommendation.Category.GENERAL,
            "title": "Review assessment warning indicators",
            "explanation": " ".join(messages) or assessment.summary,
            "recommended_action": (
                "Review the recorded warning indicators and the related "
                "field observations. Seek qualified local agricultural "
                "advice before choosing a corrective treatment."
            ),
            "priority": Recommendation.Priority.HIGH,
            "evidence": {
                **_build_assessment_evidence(assessment),
                "assessment_status": assessment.status,
                "finding_codes": [
                    finding.get("code") for finding in unknown_attention
                ],
            },
            "rule_version": RULE_VERSION,
            "is_active": True,
        }

    if unknown_monitoring:
        recommendation_specs["unmapped_monitoring_review"] = {
            "category": Recommendation.Category.GENERAL,
            "title": "Review observations that need monitoring",
            "explanation": " ".join(
                finding.get("message", "")
                for finding in unknown_monitoring
                if finding.get("message")
            ) or assessment.summary,
            "recommended_action": (
                "Continue monitoring the recorded observations and discuss "
                "changes with a qualified local agricultural adviser."
            ),
            "priority": Recommendation.Priority.MEDIUM,
            "evidence": {
                **_build_assessment_evidence(assessment),
                "assessment_status": assessment.status,
                "finding_codes": [
                    finding.get("code") for finding in unknown_monitoring
                ],
            },
            "rule_version": RULE_VERSION,
            "is_active": True,
        }

    # Provide a useful routine action when no warning rule matched.
    if not recommendation_specs:
        if assessment.status == "limited_data":
            code = "limited_data_review"
            title = "Improve field observation records"
            explanation = (
                "The assessment has limited sampling information."
            )
            action = (
                "Record representative planting stations and crop "
                "observations during the next field visit."
            )
            priority = Recommendation.Priority.LOW

        else:
            code = "routine_field_monitoring"
            title = "Continue routine field monitoring"
            explanation = (
                "No specific recommendation rule was triggered "
                "by the recorded assessment findings."
            )
            action = (
                "Continue inspecting the crop at appropriate intervals. "
                "Record crop condition, soil moisture, weed pressure, "
                "and any visible damage."
            )
            priority = Recommendation.Priority.INFORMATIONAL

        recommendation_specs[code] = {
            "category": Recommendation.Category.GENERAL,
            "title": title,
            "explanation": explanation,
            "recommended_action": action,
            "priority": priority,
            "evidence": {
                **_build_assessment_evidence(assessment),
                "assessment_status": assessment.status,
            },
            "rule_version": RULE_VERSION,
            "is_active": True,
        }

    return _sync_recommendations(
        assessment,
        "assessment",
        recommendation_specs,
    )


SEASON_RECOMMENDATION_RULES = {
    "attention_required": (
        "season_establishment_review",
        "Review establishment warnings before relying on timing",
        Recommendation.Priority.HIGH,
        "Review the latest establishment findings and the field "
        "observations behind them before relying on the maturity timeline. "
        "Seek qualified local advice where needed.",
    ),
    "insufficient_data": (
        "season_data_review",
        "Complete the information needed for a season assessment",
        Recommendation.Priority.LOW,
        "Check that the planting date, variety maturity range, and expected "
        "season-end date are recorded accurately, then reassess.",
    ),
    "season_constraint": (
        "season_timing_constraint",
        "Review the season and maturity timing",
        Recommendation.Priority.HIGH,
        "The recorded season-end date is earlier than the variety's "
        "expected maturity window. Review the dates and discuss options "
        "with a qualified local agronomist.",
    ),
    "timing_uncertain": (
        "season_timing_monitoring",
        "Monitor crop development against the expected season end",
        Recommendation.Priority.MEDIUM,
        "Continue field inspections and update crop-stage observations. "
        "The recorded dates do not determine the actual harvest date.",
    ),
    "maturity_window_elapsed": (
        "season_maturity_recheck",
        "Reinspect the crop after its expected maturity window",
        Recommendation.Priority.HIGH,
        "Check crop stage and field condition directly. An elapsed expected "
        "maturity window does not confirm that the crop is ready to harvest.",
    ),
    "maturity_reached": (
        "season_harvest_readiness",
        "Confirm field readiness before harvesting",
        Recommendation.Priority.MEDIUM,
        "Verify crop maturity and field conditions directly and seek local "
        "agronomic advice where needed. The assessment does not guarantee "
        "harvest readiness.",
    ),
    "within_maturity_window": (
        "season_routine_monitoring",
        "Continue monitoring the expected maturity window",
        Recommendation.Priority.INFORMATIONAL,
        "The recorded dates are compatible with the variety's expected "
        "maturity range. Continue field monitoring; this does not guarantee "
        "successful maturity or harvest.",
    ),
}


@transaction.atomic
def generate_remaining_season_recommendations(assessment):
    rule = SEASON_RECOMMENDATION_RULES[assessment.status]
    code, title, priority, action = rule
    recommendation_specs = {
        code: {
            "category": Recommendation.Category.SEASON,
            "title": title,
            "explanation": assessment.summary,
            "recommended_action": action,
            "priority": priority,
            "evidence": {
                **(assessment.evidence or {}),
                "assessment_status": assessment.status,
                "assessment_date": assessment.assessment_date.isoformat(),
                "expected_maturity_start": (
                    assessment.expected_maturity_start.isoformat()
                    if assessment.expected_maturity_start else None
                ),
                "expected_maturity_end": (
                    assessment.expected_maturity_end.isoformat()
                    if assessment.expected_maturity_end else None
                ),
                "expected_season_end_date": (
                    assessment.expected_season_end_date.isoformat()
                    if assessment.expected_season_end_date else None
                ),
            },
            "rule_version": RULE_VERSION,
            "is_active": True,
        },
    }
    return _sync_recommendations(
        assessment,
        "remaining_season_assessment",
        recommendation_specs,
    )
