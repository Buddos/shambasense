from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from crops.models import Crop, Variety
from farms.models import Farm, Field
from planting.models import PlantingAttempt
from inspections.models import Inspection
from recommendations.models import Recommendation

from .models import EstablishmentAssessment
from .services import assess_establishment


User = get_user_model()


class EstablishmentAssessmentTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="assessmentfarmer",
            email="assessment@example.com",
            password="SecurePassword123!",
        )

        self.farm = Farm.objects.create(
            owner=self.user,
            name="Assessment Farm",
            county="Nakuru",
            total_acreage=Decimal("10.00"),
        )

        self.field = Field.objects.create(
            farm=self.farm,
            name="Field A",
            acreage=Decimal("5.00"),
        )

        self.crop = Crop.objects.create(
            name="Maize",
        )

        self.variety = Variety.objects.create(
            crop=self.crop,
            name="Test Variety",
            maturity_days_min=120,
            maturity_days_max=150,
        )

        self.planting = PlantingAttempt.objects.create(
            field=self.field,
            crop=self.crop,
            variety=self.variety,
            planting_date=timezone.localdate() - timedelta(days=10),
            area_planted=Decimal("2.00"),
        )

    def create_inspection(self, **kwargs):
        data = {
            "planting_attempt": self.planting,
            "inspected_by": self.user,
            "inspection_date": timezone.localdate(),
            "crop_stage": Inspection.CropStage.SEEDLING,
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

    def test_no_major_warning_signs_assessment(self):
        inspection = self.create_inspection()

        assessment = assess_establishment(inspection)

        self.assertEqual(
            assessment.status,
            EstablishmentAssessment.Status.NO_MAJOR_WARNING_SIGNS,
        )

        self.assertEqual(
            assessment.emergence_percentage,
            Decimal("80.00"),
        )

    def test_dry_soil_requires_attention(self):
        inspection = self.create_inspection(
            soil_moisture=Inspection.SoilMoisture.DRY,
        )

        assessment = assess_establishment(inspection)

        self.assertEqual(
            assessment.status,
            EstablishmentAssessment.Status.ATTENTION_REQUIRED,
        )

        finding_codes = [
            finding["code"]
            for finding in assessment.findings
        ]

        self.assertIn("soil_dry", finding_codes)

    def test_pest_or_disease_signs_require_attention(self):
        inspection = self.create_inspection(
            pest_or_disease_signs=True,
        )

        assessment = assess_establishment(inspection)

        self.assertEqual(
            assessment.status,
            EstablishmentAssessment.Status.ATTENTION_REQUIRED,
        )

    def test_moderate_weed_pressure_produces_mixed_signals(self):
        inspection = self.create_inspection(
            weed_pressure=Inspection.WeedPressure.MODERATE,
        )

        assessment = assess_establishment(inspection)

        self.assertEqual(
            assessment.status,
            EstablishmentAssessment.Status.MIXED_SIGNALS,
        )

    def test_missing_emergence_data_produces_limited_data(self):
        inspection = self.create_inspection(
            planting_stations_observed=0,
            stations_with_emergence=0,
        )

        assessment = assess_establishment(inspection)

        self.assertEqual(
            assessment.status,
            EstablishmentAssessment.Status.LIMITED_DATA,
        )

        self.assertIsNone(assessment.emergence_percentage)

    def test_attention_takes_priority_over_monitoring(self):
        inspection = self.create_inspection(
            soil_moisture=Inspection.SoilMoisture.DRY,
            weed_pressure=Inspection.WeedPressure.MODERATE,
        )

        assessment = assess_establishment(inspection)

        self.assertEqual(
            assessment.status,
            EstablishmentAssessment.Status.ATTENTION_REQUIRED,
        )

    def test_assessment_records_inspection_evidence(self):
        inspection = self.create_inspection(
            healthy_plant_count=12,
            damaged_plant_count=3,
        )

        assessment = assess_establishment(inspection)

        self.assertEqual(assessment.healthy_plant_count, 12)
        self.assertEqual(assessment.damaged_plant_count, 3)

    def test_assessment_is_updated_instead_of_duplicated(self):
        inspection = self.create_inspection()

        first_assessment = assess_establishment(inspection)

        inspection.soil_moisture = Inspection.SoilMoisture.DRY
        inspection.save()

        second_assessment = assess_establishment(inspection)

        self.assertEqual(
            first_assessment.pk,
            second_assessment.pk,
        )

        self.assertEqual(
            EstablishmentAssessment.objects.filter(
                inspection=inspection
            ).count(),
            1,
        )

        self.assertEqual(
            second_assessment.status,
            EstablishmentAssessment.Status.ATTENTION_REQUIRED,
        )


class RecommendationIntegrationTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="recommendationfarmer",
            email="recommendation@example.com",
            password="SecurePassword123!",
        )

        self.farm = Farm.objects.create(
            owner=self.user,
            name="Recommendation Farm",
            county="Nakuru",
            total_acreage=Decimal("10.00"),
        )

        self.field = Field.objects.create(
            farm=self.farm,
            name="Field A",
            acreage=Decimal("5.00"),
        )

        self.crop = Crop.objects.create(
            name="Integration Maize",
        )

        self.variety = Variety.objects.create(
            crop=self.crop,
            name="Integration Variety",
            maturity_days_min=120,
            maturity_days_max=150,
        )

        self.planting = PlantingAttempt.objects.create(
            field=self.field,
            crop=self.crop,
            variety=self.variety,
            planting_date=timezone.localdate() - timedelta(days=10),
            area_planted=Decimal("2.00"),
        )

    def create_inspection(self, **kwargs):
        data = {
            "planting_attempt": self.planting,
            "inspected_by": self.user,
            "inspection_date": timezone.localdate(),
            "crop_stage": Inspection.CropStage.SEEDLING,
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

    def test_assessment_automatically_generates_recommendation(self):
        inspection = self.create_inspection(
            soil_moisture=Inspection.SoilMoisture.DRY,
        )

        assessment = assess_establishment(inspection)

        recommendation = Recommendation.objects.get(
            assessment=assessment,
            code="soil_dry",
        )

        self.assertEqual(
            recommendation.title,
            "Investigate dry soil conditions",
        )

        self.assertEqual(
            recommendation.priority,
            Recommendation.Priority.HIGH,
        )

        self.assertTrue(recommendation.is_active)

    def test_rerunning_assessment_does_not_duplicate_recommendations(self):
        inspection = self.create_inspection(
            soil_moisture=Inspection.SoilMoisture.DRY,
        )

        first_assessment = assess_establishment(inspection)

        first_recommendation = Recommendation.objects.get(
            assessment=first_assessment,
            code="soil_dry",
        )

        assess_establishment(inspection)

        self.assertEqual(
            Recommendation.objects.filter(
                assessment=first_assessment,
                code="soil_dry",
            ).count(),
            1,
        )

        self.assertEqual(
            Recommendation.objects.filter(
                assessment=first_assessment,
            ).count(),
            1,
        )

        self.assertEqual(
            Recommendation.objects.get(
                assessment=first_assessment,
                code="soil_dry",
            ).pk,
            first_recommendation.pk,
        )

    def test_reassessment_preserves_farmer_progress(self):
        inspection = self.create_inspection(
            soil_moisture=Inspection.SoilMoisture.DRY,
        )

        assessment = assess_establishment(inspection)

        recommendation = Recommendation.objects.get(
            assessment=assessment,
            code="soil_dry",
        )

        follow_up_date = timezone.localdate() + timedelta(days=7)

        recommendation.status = Recommendation.Status.IN_PROGRESS
        recommendation.follow_up_date = follow_up_date
        recommendation.save()

        inspection.soil_moisture = Inspection.SoilMoisture.DRY
        inspection.save()

        assess_establishment(inspection)

        recommendation.refresh_from_db()

        self.assertEqual(
            recommendation.status,
            Recommendation.Status.IN_PROGRESS,
        )

        self.assertEqual(
            recommendation.follow_up_date,
            follow_up_date,
        )

        self.assertTrue(recommendation.is_active)

    def test_changed_inspection_deactivates_old_recommendation(self):
        inspection = self.create_inspection(
            soil_moisture=Inspection.SoilMoisture.DRY,
        )

        assessment = assess_establishment(inspection)

        old_recommendation = Recommendation.objects.get(
            assessment=assessment,
            code="soil_dry",
        )

        # Simulate farmer progress on the original recommendation.
        follow_up_date = timezone.localdate() + timedelta(days=5)

        old_recommendation.status = Recommendation.Status.IN_PROGRESS
        old_recommendation.follow_up_date = follow_up_date
        old_recommendation.save()

        # Update the inspection with new observations.
        inspection.soil_moisture = Inspection.SoilMoisture.WATERLOGGED
        inspection.save()

        assess_establishment(inspection)

        old_recommendation.refresh_from_db()

        # The old recommendation must remain as historical evidence.
        self.assertTrue(
            Recommendation.objects.filter(
                pk=old_recommendation.pk,
            ).exists()
        )

        self.assertFalse(old_recommendation.is_active)

        # Farmer progress must remain intact.
        self.assertEqual(
            old_recommendation.status,
            Recommendation.Status.IN_PROGRESS,
        )

        self.assertEqual(
            old_recommendation.follow_up_date,
            follow_up_date,
        )

        # The new recommendation must be active.
        new_recommendation = Recommendation.objects.get(
            assessment=assessment,
            code="soil_waterlogged",
        )

        self.assertTrue(new_recommendation.is_active)

        self.assertEqual(
            new_recommendation.priority,
            Recommendation.Priority.HIGH,
        )

    def test_old_recommendation_is_reactivated_if_finding_returns(self):
        inspection = self.create_inspection(
            soil_moisture=Inspection.SoilMoisture.DRY,
        )

        assessment = assess_establishment(inspection)

        dry_recommendation = Recommendation.objects.get(
            assessment=assessment,
            code="soil_dry",
        )

        # Change dry soil to waterlogged.
        inspection.soil_moisture = Inspection.SoilMoisture.WATERLOGGED
        inspection.save()

        assess_establishment(inspection)

        dry_recommendation.refresh_from_db()
        self.assertFalse(dry_recommendation.is_active)

        # Change the observation back to dry.
        inspection.soil_moisture = Inspection.SoilMoisture.DRY
        inspection.save()

        assess_establishment(inspection)

        dry_recommendation.refresh_from_db()

        self.assertTrue(dry_recommendation.is_active)

        # It must reuse the original record, not create a duplicate.
        self.assertEqual(
            Recommendation.objects.filter(
                assessment=assessment,
                code="soil_dry",
            ).count(),
            1,
        )
