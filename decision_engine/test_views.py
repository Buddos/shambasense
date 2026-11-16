from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from crops.models import Crop, Variety
from farms.models import Farm, Field
from inspections.models import Inspection

from .models import EstablishmentAssessment, RemainingSeasonAssessment
from .remaining_season import assess_remaining_season
from .services import assess_establishment


User = get_user_model()


class AssessmentViewTests(TestCase):
    def setUp(self):
        self.today = timezone.localdate()

        self.user = User.objects.create_user(
            username="assessment_view_farmer",
            email="assessment_view@example.com",
            password="SecurePassword123!",
        )

        self.other_user = User.objects.create_user(
            username="other_assessment_farmer",
            email="other_assessment@example.com",
            password="SecurePassword123!",
        )

        self.farm = Farm.objects.create(
            owner=self.user,
            name="My Assessment Farm",
            county="Nakuru",
            total_acreage=Decimal("10.00"),
        )

        self.field = Field.objects.create(
            farm=self.farm,
            name="Field A",
            acreage=Decimal("5.00"),
        )

        self.other_farm = Farm.objects.create(
            owner=self.other_user,
            name="Other Farmer Farm",
            county="Nakuru",
            total_acreage=Decimal("5.00"),
        )

        self.other_field = Field.objects.create(
            farm=self.other_farm,
            name="Other Field",
            acreage=Decimal("3.00"),
        )

        self.crop = Crop.objects.create(name="View Test Maize")

        self.variety = Variety.objects.create(
            crop=self.crop,
            name="View Test Variety",
            maturity_days_min=120,
            maturity_days_max=150,
        )

        self.planting = self.create_planting(
            self.field,
            "My Planting",
        )

        self.other_planting = self.create_planting(
            self.other_field,
            "Other Planting",
        )

    def create_planting(self, field, name):
        return field.planting_attempts.create(
            crop=self.crop,
            variety=self.variety,
            planting_date=self.today - timedelta(days=60),
            expected_season_end_date=self.today + timedelta(days=200),
            area_planted=Decimal("1.00"),
            notes=name,
        )

    def create_inspection(self, planting, user, **overrides):
        data = {
            "planting_attempt": planting,
            "inspected_by": user,
            "inspection_date": self.today,
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
        data.update(overrides)
        return Inspection.objects.create(**data)

    def create_establishment_assessment(
        self,
        planting=None,
        user=None,
        **overrides,
    ):
        planting = planting or self.planting
        user = user or self.user

        inspection = self.create_inspection(
            planting,
            user,
            **overrides,
        )

        assessment = assess_establishment(inspection)
        return inspection, assessment

    def test_assessment_history_requires_login(self):
        response = self.client.get(
            reverse("decision_engine:history")
        )

        self.assertEqual(response.status_code, 302)

    def test_farmer_can_view_assessment_history(self):
        self.create_establishment_assessment()

        self.client.force_login(self.user)

        response = self.client.get(
            reverse("decision_engine:history")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "assessments/history.html")
        self.assertEqual(response.context["establishment_count"], 1)
        self.assertContains(response, "Crop Establishment")

    def test_assessment_history_only_shows_own_records(self):
        self.create_establishment_assessment()

        self.create_establishment_assessment(
            planting=self.other_planting,
            user=self.other_user,
        )

        self.client.force_login(self.user)

        response = self.client.get(
            reverse("decision_engine:history")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["establishment_count"], 1)
        self.assertContains(response, "My Assessment Farm")
        self.assertNotContains(response, "Other Farmer Farm")

    def test_empty_assessment_history_loads(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("decision_engine:history")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["establishment_count"], 0)
        self.assertEqual(response.context["season_count"], 0)
        self.assertContains(
            response,
            "No establishment assessments have been generated yet.",
        )

    def test_establishment_detail_displays_assessment_and_recommendations(self):
        inspection, assessment = self.create_establishment_assessment(
            soil_moisture=Inspection.SoilMoisture.DRY,
        )

        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "decision_engine:establishment_detail",
                args=[inspection.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "assessments/establishment_detail.html",
        )
        self.assertEqual(
            response.context["assessment"].pk,
            assessment.pk,
        )
        self.assertContains(response, "Crop Establishment Assessment")
        self.assertContains(response, assessment.get_status_display())
        self.assertContains(response, "Generated Recommendations")
        self.assertTrue(response.context["recommendations"].exists())

    def test_farmer_cannot_view_another_farmers_establishment_assessment(self):
        inspection, _ = self.create_establishment_assessment(
            planting=self.other_planting,
            user=self.other_user,
        )

        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "decision_engine:establishment_detail",
                args=[inspection.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_remaining_season_detail_displays_assessment_evidence(self):
        assessment = assess_remaining_season(
            self.planting,
            assessment_date=self.today,
        )

        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "decision_engine:remaining_season_detail",
                args=[self.planting.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "assessments/remaining_season_detail.html",
        )
        self.assertEqual(
            response.context["assessment"].pk,
            assessment.pk,
        )
        self.assertContains(response, "Assessment Evidence")
        self.assertContains(response, "Expected Maturity Start")
        self.assertContains(response, "Reassess Remaining Season")

    def test_farmer_cannot_view_another_farmers_remaining_season_assessment(self):
        assess_remaining_season(
            self.other_planting,
            assessment_date=self.today,
        )

        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "decision_engine:remaining_season_detail",
                args=[self.other_planting.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_assessments_navigation_link_is_available(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("decision_engine:history")
        )

        self.assertContains(
            response,
            reverse("decision_engine:history"),
        )
        self.assertContains(response, "Assessments")


class AssessmentViewAuthenticationTests(TestCase):
    def test_establishment_detail_requires_login(self):
        response = self.client.get(
            reverse(
                "decision_engine:establishment_detail",
                args=[999],
            )
        )

        self.assertEqual(response.status_code, 302)

    def test_remaining_season_detail_requires_login(self):
        response = self.client.get(
            reverse(
                "decision_engine:remaining_season_detail",
                args=[999],
            )
        )

        self.assertEqual(response.status_code, 302)
