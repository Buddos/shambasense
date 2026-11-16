from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from crops.models import Crop, Variety
from decision_engine.models import RemainingSeasonAssessment
from farms.models import Farm, Field
from planting.models import PlantingAttempt


class RemainingSeasonViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        today = timezone.localdate()

        cls.farmer = User.objects.create_user(
            username="season_farmer",
            email="season_farmer@example.com",
            password="test-password-123",
        )

        cls.other_farmer = User.objects.create_user(
            username="other_farmer",
            email="other_farmer@example.com",
            password="test-password-123",
        )

        cls.farm = Farm.objects.create(
            owner=cls.farmer,
            name="Test Farm",
            county="Nakuru",
            total_acreage=5,
        )

        cls.field = Field.objects.create(
            farm=cls.farm,
            name="Field A",
            acreage=2,
            soil_type="Loam",
        )

        cls.crop = Crop.objects.create(
            name="Test Maize",
            crop_type=Crop.CropType.CEREAL,
        )

        cls.variety = Variety.objects.create(
            crop=cls.crop,
            name="Test Hybrid",
            maturity_days_min=90,
            maturity_days_max=110,
        )

        cls.planting = PlantingAttempt.objects.create(
            field=cls.field,
            crop=cls.crop,
            variety=cls.variety,
            planting_date=today - timedelta(days=30),
            expected_season_end_date=today + timedelta(days=100),
            area_planted=1,
            planting_method=PlantingAttempt.PlantingMethod.ROW,
        )

        other_farm = Farm.objects.create(
            owner=cls.other_farmer,
            name="Other Farm",
            county="Nakuru",
            total_acreage=3,
        )

        other_field = Field.objects.create(
            farm=other_farm,
            name="Other Field",
            acreage=2,
        )

        cls.other_planting = PlantingAttempt.objects.create(
            field=other_field,
            crop=cls.crop,
            variety=cls.variety,
            planting_date=today - timedelta(days=20),
            expected_season_end_date=today + timedelta(days=120),
            area_planted=1,
        )

    def setUp(self):
        self.detail_url = reverse(
            "planting:detail",
            args=[self.planting.pk],
        )
        self.assessment_url = reverse(
            "planting:assess_remaining_season",
            args=[self.planting.pk],
        )

    def test_detail_page_displays_without_creating_assessment(self):
        self.client.login(
            username="season_farmer",
            password="test-password-123",
        )

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Remaining-Season Assessment")
        self.assertContains(response, "Run Assessment")
        self.assertIsNone(
            getattr(
                self.planting,
                "remaining_season_assessment",
                None,
            )
        )
        self.assertEqual(
            RemainingSeasonAssessment.objects.count(),
            0,
        )

    def test_post_creates_remaining_season_assessment(self):
        self.client.login(
            username="season_farmer",
            password="test-password-123",
        )

        response = self.client.post(self.assessment_url)

        self.assertRedirects(response, self.detail_url)

        assessment = RemainingSeasonAssessment.objects.get(
            planting_attempt=self.planting,
        )

        self.assertEqual(
            assessment.status,
            RemainingSeasonAssessment.Status.WITHIN_MATURITY_WINDOW,
        )
        self.assertEqual(
            assessment.expected_season_end_date,
            self.planting.expected_season_end_date,
        )
        self.assertTrue(assessment.summary)

    def test_post_refreshes_existing_assessment_without_duplicates(self):
        self.client.login(
            username="season_farmer",
            password="test-password-123",
        )

        self.client.post(self.assessment_url)

        assessment = RemainingSeasonAssessment.objects.get(
            planting_attempt=self.planting,
        )
        original_id = assessment.pk

        updated_season_end = (
            timezone.localdate() + timedelta(days=40)
        )
        self.planting.expected_season_end_date = updated_season_end
        self.planting.save(
            update_fields=["expected_season_end_date", "updated_at"]
        )

        response = self.client.post(self.assessment_url)

        self.assertRedirects(response, self.detail_url)

        assessment.refresh_from_db()

        self.assertEqual(assessment.pk, original_id)
        self.assertEqual(
            RemainingSeasonAssessment.objects.filter(
                planting_attempt=self.planting,
            ).count(),
            1,
        )
        self.assertEqual(
            assessment.expected_season_end_date,
            updated_season_end,
        )
        self.assertEqual(
            assessment.status,
            RemainingSeasonAssessment.Status.SEASON_CONSTRAINT,
        )

    def test_detail_page_displays_existing_assessment(self):
        self.client.login(
            username="season_farmer",
            password="test-password-123",
        )

        self.client.post(self.assessment_url)

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Refresh Assessment")
        self.assertContains(response, "Expected Maturity Starts")
        self.assertContains(response, "Recorded Season End")

    def test_another_farmer_cannot_view_planting_detail(self):
        self.client.login(
            username="other_farmer",
            password="test-password-123",
        )

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 404)

    def test_another_farmer_cannot_run_assessment(self):
        self.client.login(
            username="other_farmer",
            password="test-password-123",
        )

        response = self.client.post(self.assessment_url)

        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            RemainingSeasonAssessment.objects.filter(
                planting_attempt=self.planting,
            ).exists()
        )

    def test_anonymous_user_is_redirected_from_detail(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_anonymous_user_cannot_run_assessment(self):
        response = self.client.post(self.assessment_url)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            RemainingSeasonAssessment.objects.filter(
                planting_attempt=self.planting,
            ).exists()
        )

    def test_assessment_endpoint_rejects_get_requests(self):
        self.client.login(
            username="season_farmer",
            password="test-password-123",
        )

        response = self.client.get(self.assessment_url)

        self.assertEqual(response.status_code, 405)
        self.assertEqual(
            RemainingSeasonAssessment.objects.count(),
            0,
        )
