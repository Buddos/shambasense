from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from crops.models import Crop, Variety
from decision_engine.models import (
    EstablishmentAssessment,
    RemainingSeasonAssessment,
)
from farms.models import Farm, Field
from inspections.models import Inspection
from planting.models import PlantingAttempt
from recommendations.models import Recommendation


User = get_user_model()


class DashboardHomeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="dashboard_farmer",
            email="dashboard@example.com",
            password="testpass123",
            role=User.Role.FARMER,
        )

        self.other_user = User.objects.create_user(
            username="other_farmer",
            email="other@example.com",
            password="testpass123",
            role=User.Role.FARMER,
        )

        self.farm = Farm.objects.create(
            owner=self.user,
            name="Dashboard Farm",
            county="Nakuru",
            total_acreage=2,
        )

        self.field = Field.objects.create(
            farm=self.farm,
            name="Main Field",
            acreage=1,
            soil_type="Loam",
        )

        self.other_farm = Farm.objects.create(
            owner=self.other_user,
            name="Other Farm",
            county="Nakuru",
            total_acreage=3,
        )

        self.other_field = Field.objects.create(
            farm=self.other_farm,
            name="Other Field",
            acreage=1,
            soil_type="Clay",
        )

        self.crop = Crop.objects.create(
            name="Dashboard Maize",
            crop_type=Crop.CropType.CEREAL,
        )

        self.variety = Variety.objects.create(
            crop=self.crop,
            name="Dashboard Variety",
            maturity_days_min=90,
            maturity_days_max=120,
        )

    def create_planting(self, field, status=PlantingAttempt.Status.ACTIVE):
        return PlantingAttempt.objects.create(
            field=field,
            crop=self.crop,
            variety=self.variety,
            planting_date=date.today() - timedelta(days=20),
            expected_season_end_date=date.today() + timedelta(days=100),
            area_planted=0.5,
            status=status,
        )

    def create_inspection(self, planting):
        return Inspection.objects.create(
            planting_attempt=planting,
            inspected_by=self.user,
            inspection_date=date.today(),
            crop_stage=Inspection.CropStage.VEGETATIVE,
            planting_stations_observed=10,
            stations_with_emergence=9,
            healthy_plant_count=8,
            damaged_plant_count=1,
            crop_condition=Inspection.CropCondition.GOOD,
            soil_moisture=Inspection.SoilMoisture.ADEQUATE,
            weed_pressure=Inspection.WeedPressure.LOW,
            pest_or_disease_signs=False,
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard:home"))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('dashboard:home')}",
        )

    def test_dashboard_returns_real_counts(self):
        planting = self.create_planting(self.field)
        self.create_planting(
            self.field,
            status=PlantingAttempt.Status.COMPLETED,
        )

        self.create_inspection(planting)

        self.client.login(
            username="dashboard_farmer",
            password="testpass123",
        )

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context["farms_count"], 1)
        self.assertEqual(response.context["fields_count"], 1)
        self.assertEqual(response.context["planting_count"], 2)
        self.assertEqual(response.context["active_planting_count"], 1)
        self.assertEqual(response.context["inspections_count"], 1)

    def test_dashboard_does_not_include_another_farmers_data(self):
        self.create_planting(self.field)
        self.create_planting(self.other_field)

        self.client.login(
            username="dashboard_farmer",
            password="testpass123",
        )

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.context["farms_count"], 1)
        self.assertEqual(response.context["fields_count"], 1)
        self.assertEqual(response.context["planting_count"], 1)

    def test_dashboard_shows_establishment_assessment(self):
        planting = self.create_planting(self.field)
        inspection = self.create_inspection(planting)

        assessment = EstablishmentAssessment.objects.create(
            inspection=inspection,
            status=EstablishmentAssessment.Status.NO_MAJOR_WARNING_SIGNS,
            emergence_percentage=90,
            healthy_plant_count=8,
            damaged_plant_count=1,
            findings=[],
            summary="No major warning signs were observed.",
        )

        self.client.login(
            username="dashboard_farmer",
            password="testpass123",
        )

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(
            response.context["latest_establishment_assessment"],
            assessment,
        )

    def test_dashboard_shows_remaining_season_assessment(self):
        planting = self.create_planting(self.field)

        assessment = RemainingSeasonAssessment.objects.create(
            planting_attempt=planting,
            status=RemainingSeasonAssessment.Status.WITHIN_MATURITY_WINDOW,
            assessment_date=date.today(),
            expected_maturity_start=date.today() + timedelta(days=70),
            expected_maturity_end=date.today() + timedelta(days=100),
            expected_season_end_date=date.today() + timedelta(days=100),
            days_after_planting=20,
            summary="The expected maturity window fits within the season.",
            evidence={},
        )

        self.client.login(
            username="dashboard_farmer",
            password="testpass123",
        )

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(
            response.context["latest_remaining_season_assessment"],
            assessment,
        )

    def test_dashboard_counts_outstanding_recommendations(self):
        planting = self.create_planting(self.field)
        inspection = self.create_inspection(planting)

        assessment = EstablishmentAssessment.objects.create(
            inspection=inspection,
            status=EstablishmentAssessment.Status.ATTENTION_REQUIRED,
            emergence_percentage=50,
            healthy_plant_count=2,
            damaged_plant_count=5,
            findings=[],
            summary="Attention is required.",
        )

        Recommendation.objects.create(
            assessment=assessment,
            code="test_recommendation",
            category=Recommendation.Category.GENERAL,
            title="Test recommendation",
            explanation="Test explanation.",
            recommended_action="Take action.",
            priority=Recommendation.Priority.HIGH,
            status=Recommendation.Status.PENDING,
        )

        Recommendation.objects.create(
            assessment=assessment,
            code="completed_recommendation",
            category=Recommendation.Category.GENERAL,
            title="Completed recommendation",
            explanation="Completed explanation.",
            recommended_action="No further action.",
            priority=Recommendation.Priority.HIGH,
            status=Recommendation.Status.COMPLETED,
        )

        self.client.login(
            username="dashboard_farmer",
            password="testpass123",
        )

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(
            response.context["outstanding_recommendations_count"],
            1,
        )

        self.assertEqual(
            response.context["high_priority_recommendations_count"],
            1,
        )

    def test_dashboard_has_empty_states_for_new_farmer(self):
        self.client.login(
            username="dashboard_farmer",
            password="testpass123",
        )

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["farms_count"], 1)
        self.assertEqual(response.context["fields_count"], 1)
        self.assertEqual(response.context["planting_count"], 0)
        self.assertEqual(response.context["inspections_count"], 0)
        self.assertEqual(
            response.context["outstanding_recommendations_count"],
            0,
        )
        self.assertIsNone(
            response.context["latest_inspection"],
        )
        self.assertIsNone(
            response.context["latest_establishment_assessment"],
        )
        self.assertIsNone(
            response.context["latest_remaining_season_assessment"],
        )

    def test_dashboard_counts_all_planting_lifecycle_statuses(self):
        self.create_planting(self.field, PlantingAttempt.Status.ACTIVE)
        self.create_planting(self.field, PlantingAttempt.Status.COMPLETED)
        self.create_planting(self.field, PlantingAttempt.Status.ABANDONED)
        self.create_planting(self.field, PlantingAttempt.Status.REPLACED)

        self.client.login(
            username="dashboard_farmer",
            password="testpass123",
        )

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.context["planting_count"], 4)
        self.assertEqual(response.context["active_planting_count"], 1)
        self.assertEqual(response.context["completed_planting_count"], 1)
        self.assertEqual(response.context["abandoned_planting_count"], 1)
        self.assertEqual(response.context["replaced_planting_count"], 1)

    def test_dashboard_counts_establishment_attention(self):
        planting = self.create_planting(self.field)
        inspection = self.create_inspection(planting)

        EstablishmentAssessment.objects.create(
            inspection=inspection,
            status=EstablishmentAssessment.Status.ATTENTION_REQUIRED,
            emergence_percentage=40,
            healthy_plant_count=2,
            damaged_plant_count=5,
            findings=[],
            summary="Attention is required.",
        )

        self.client.login(
            username="dashboard_farmer",
            password="testpass123",
        )

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(
            response.context["establishment_attention_count"],
            1,
        )
        self.assertEqual(response.context["total_attention_count"], 1)

    def test_dashboard_counts_remaining_season_constraints(self):
        planting = self.create_planting(self.field)

        RemainingSeasonAssessment.objects.create(
            planting_attempt=planting,
            status=RemainingSeasonAssessment.Status.SEASON_CONSTRAINT,
            assessment_date=date.today(),
            expected_maturity_start=date.today() + timedelta(days=90),
            expected_maturity_end=date.today() + timedelta(days=120),
            expected_season_end_date=date.today() + timedelta(days=60),
            days_after_planting=20,
            summary="The season end precedes the expected maturity window.",
            evidence={},
        )

        self.client.login(
            username="dashboard_farmer",
            password="testpass123",
        )

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.context["season_attention_count"], 1)
        self.assertEqual(response.context["total_attention_count"], 1)

    def test_dashboard_does_not_count_other_farmers_attention(self):
        other_planting = self.create_planting(self.other_field)
        other_inspection = self.create_inspection(other_planting)

        EstablishmentAssessment.objects.create(
            inspection=other_inspection,
            status=EstablishmentAssessment.Status.ATTENTION_REQUIRED,
            emergence_percentage=30,
            healthy_plant_count=1,
            damaged_plant_count=5,
            findings=[],
            summary="Other farmer's assessment.",
        )

        self.client.login(
            username="dashboard_farmer",
            password="testpass123",
        )

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(
            response.context["establishment_attention_count"],
            0,
        )
        self.assertEqual(response.context["total_attention_count"], 0)
