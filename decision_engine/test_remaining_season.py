from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from crops.models import Crop, Variety
from farms.models import Farm, Field
from inspections.models import Inspection
from planting.models import PlantingAttempt
from recommendations.models import Recommendation

from .models import RemainingSeasonAssessment
from .remaining_season import assess_remaining_season
from .services import assess_establishment


User = get_user_model()


class RemainingSeasonAssessmentTests(TestCase):

    def setUp(self):
        self.today = timezone.localdate()

        self.user = User.objects.create_user(
            username="seasonfarmer",
            email="seasonfarmer@example.com",
            password="SecurePassword123!",
        )

        self.farm = Farm.objects.create(
            owner=self.user,
            name="Season Assessment Farm",
            county="Nakuru",
            total_acreage=Decimal("10.00"),
        )

        self.field = Field.objects.create(
            farm=self.farm,
            name="Season Field",
            acreage=Decimal("5.00"),
        )

        self.crop = Crop.objects.create(name="Season Maize")

        self.variety = Variety.objects.create(
            crop=self.crop,
            name="Season Variety",
            maturity_days_min=120,
            maturity_days_max=150,
        )

        self.planting = PlantingAttempt.objects.create(
            field=self.field,
            crop=self.crop,
            variety=self.variety,
            planting_date=self.today - timedelta(days=60),
            expected_season_end_date=self.today + timedelta(days=200),
            area_planted=Decimal("2.00"),
        )

    def create_inspection(self, **kwargs):
        data = {
            "planting_attempt": self.planting,
            "inspected_by": self.user,
            "inspection_date": self.today,
            "crop_stage": Inspection.CropStage.VEGETATIVE,
            "planting_stations_observed": 10,
            "stations_with_emergence": 8,
            "healthy_plant_count": 8,
            "damaged_plant_count": 0,
            "crop_condition": Inspection.CropCondition.GOOD,
            "soil_moisture": Inspection.SoilMoisture.ADEQUATE,
            "weed_pressure": Inspection.WeedPressure.NONE,
            "pest_or_disease_signs": False,
        }
        data.update(kwargs)
        return Inspection.objects.create(**data)

    def test_within_maturity_window(self):
        assessment = assess_remaining_season(
            self.planting,
            assessment_date=self.today,
        )

        self.assertEqual(
            assessment.status,
            RemainingSeasonAssessment.Status.WITHIN_MATURITY_WINDOW,
        )

        self.assertEqual(
            assessment.expected_maturity_start,
            self.planting.planting_date + timedelta(days=120),
        )

        self.assertEqual(
            assessment.expected_maturity_end,
            self.planting.planting_date + timedelta(days=150),
        )

    def test_season_constraint_when_season_ends_before_maturity_window(self):
        self.planting.expected_season_end_date = (
            self.planting.planting_date + timedelta(days=100)
        )
        self.planting.save()

        assessment = assess_remaining_season(
            self.planting,
            assessment_date=self.today,
        )

        self.assertEqual(
            assessment.status,
            RemainingSeasonAssessment.Status.SEASON_CONSTRAINT,
        )

    def test_timing_uncertain_when_season_ends_inside_maturity_range(self):
        self.planting.expected_season_end_date = (
            self.planting.planting_date + timedelta(days=135)
        )
        self.planting.save()

        assessment = assess_remaining_season(
            self.planting,
            assessment_date=self.today,
        )

        self.assertEqual(
            assessment.status,
            RemainingSeasonAssessment.Status.TIMING_UNCERTAIN,
        )

    def test_missing_season_end_date_produces_insufficient_data(self):
        self.planting.expected_season_end_date = None
        self.planting.save()

        assessment = assess_remaining_season(
            self.planting,
            assessment_date=self.today,
        )

        self.assertEqual(
            assessment.status,
            RemainingSeasonAssessment.Status.INSUFFICIENT_DATA,
        )

    def test_attention_required_when_latest_establishment_assessment_has_warnings(self):
        inspection = self.create_inspection(
            soil_moisture=Inspection.SoilMoisture.DRY,
        )
        assess_establishment(inspection)

        assessment = assess_remaining_season(
            self.planting,
            assessment_date=self.today,
        )

        self.assertEqual(
            assessment.status,
            RemainingSeasonAssessment.Status.ATTENTION_REQUIRED,
        )
        self.assertEqual(assessment.latest_inspection, inspection)

    def test_maturity_reached_when_latest_inspection_records_maturity(self):
        inspection = self.create_inspection(
            crop_stage=Inspection.CropStage.MATURITY,
        )

        assessment = assess_remaining_season(
            self.planting,
            assessment_date=self.today,
        )

        self.assertEqual(
            assessment.status,
            RemainingSeasonAssessment.Status.MATURITY_REACHED,
        )
        self.assertEqual(assessment.latest_inspection, inspection)

    def test_maturity_window_elapsed_without_maturity_record(self):
        assessment_date = (
            self.planting.planting_date + timedelta(days=160)
        )

        assessment = assess_remaining_season(
            self.planting,
            assessment_date=assessment_date,
        )

        self.assertEqual(
            assessment.status,
            RemainingSeasonAssessment.Status.MATURITY_WINDOW_ELAPSED,
        )

    def test_reassessment_updates_existing_record(self):
        first = assess_remaining_season(
            self.planting,
            assessment_date=self.today,
        )

        self.planting.expected_season_end_date = (
            self.planting.planting_date + timedelta(days=100)
        )
        self.planting.save()

        second = assess_remaining_season(
            self.planting,
            assessment_date=self.today,
        )

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(
            RemainingSeasonAssessment.objects.filter(
                planting_attempt=self.planting,
            ).count(),
            1,
        )
        self.assertEqual(
            second.status,
            RemainingSeasonAssessment.Status.SEASON_CONSTRAINT,
        )

    def test_assessment_stores_explainable_evidence(self):
        inspection = self.create_inspection()

        assessment = assess_remaining_season(
            self.planting,
            assessment_date=self.today,
        )

        self.assertEqual(
            assessment.evidence["planting_date"],
            self.planting.planting_date.isoformat(),
        )
        self.assertEqual(
            assessment.evidence["latest_inspection_id"],
            inspection.pk,
        )
        self.assertEqual(
            assessment.evidence["maturity_days_min"],
            120,
        )
        self.assertEqual(
            assessment.evidence["crop_stage"],
            inspection.crop_stage,
        )
        self.assertEqual(
            assessment.evidence["planting_stations_observed"],
            inspection.planting_stations_observed,
        )
        self.assertEqual(
            assessment.evidence["stations_with_emergence"],
            inspection.stations_with_emergence,
        )
        recommendation = Recommendation.objects.get(
            remaining_season_assessment=assessment,
            is_active=True,
        )
        self.assertEqual(
            recommendation.evidence["crop_stage"],
            inspection.crop_stage,
        )
        self.assertEqual(
            recommendation.evidence["planting_stations_observed"],
            inspection.planting_stations_observed,
        )
        self.assertEqual(assessment.rule_version, "1.0")
