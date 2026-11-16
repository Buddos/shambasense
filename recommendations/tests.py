from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from crops.models import Crop, Variety
from decision_engine.models import EstablishmentAssessment
from farms.models import Farm, Field
from inspections.models import Inspection
from planting.models import PlantingAttempt

from .models import Recommendation


User = get_user_model()


class RecommendationTestMixin:
    def create_user(self, username):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="TestPassword123!",
            first_name=username.title(),
        )

    def create_recommendation(self, owner, code="soil_dry"):
        farm = Farm.objects.create(
            owner=owner,
            name=f"{owner.username} Farm",
            county="Nakuru",
            sub_county="Njoro",
            total_acreage=2,
        )

        field = Field.objects.create(
            farm=farm,
            name="Field A",
            acreage=1,
            soil_type="Loam",
        )

        crop = Crop.objects.create(
            name=f"Maize-{owner.username}",
            crop_type=Crop.CropType.CEREAL,
        )

        variety = Variety.objects.create(
            crop=crop,
            name="Test Variety",
            maturity_days_min=90,
            maturity_days_max=120,
        )

        planting = PlantingAttempt.objects.create(
            field=field,
            crop=crop,
            variety=variety,
            planting_date=date.today() - timedelta(days=14),
            area_planted=1,
            planting_method=PlantingAttempt.PlantingMethod.ROW,
            status=PlantingAttempt.Status.ACTIVE,
        )

        inspection = Inspection.objects.create(
            planting_attempt=planting,
            inspected_by=owner,
            inspection_date=date.today(),
            crop_stage=Inspection.CropStage.VEGETATIVE,
            planting_stations_observed=10,
            stations_with_emergence=8,
            healthy_plant_count=6,
            damaged_plant_count=2,
            crop_condition=Inspection.CropCondition.FAIR,
            soil_moisture=Inspection.SoilMoisture.DRY,
            weed_pressure=Inspection.WeedPressure.NONE,
            pest_or_disease_signs=False,
        )

        assessment = EstablishmentAssessment.objects.create(
            inspection=inspection,
            status=EstablishmentAssessment.Status.MIXED_SIGNALS,
            emergence_percentage=80,
            healthy_plant_count=6,
            damaged_plant_count=2,
            findings=[
                {
                    "code": code,
                    "level": "attention",
                    "message": "Soil moisture was recorded as dry.",
                }
            ],
            summary="Assessment generated for testing.",
        )

        return Recommendation.objects.create(
            assessment=assessment,
            code=code,
            category=Recommendation.Category.WATER,
            title=f"Investigate dry soil conditions - {owner.username}",
            explanation="Dry soil conditions were observed.",
            recommended_action="Check soil moisture at representative locations.",
            priority=Recommendation.Priority.HIGH,
            status=Recommendation.Status.PENDING,
            evidence={
                "finding_code": code,
                "inspection_id": inspection.pk,
                "soil_moisture": "dry",
            },
            rule_version="1.0",
        )


class RecommendationListTests(RecommendationTestMixin, TestCase):

    def setUp(self):
        self.user = self.create_user("farmer")
        self.other_user = self.create_user("other")

        self.recommendation = self.create_recommendation(self.user)
        self.other_recommendation = self.create_recommendation(
            self.other_user,
            code="other_soil_dry",
        )

    def test_unauthenticated_user_is_redirected(self):
        response = self.client.get(reverse("recommendations:list"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_authenticated_user_sees_only_own_recommendations(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("recommendations:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            self.recommendation.title,
        )
        self.assertNotContains(
            response,
            self.other_recommendation.title,
        )

    def test_empty_list_is_handled(self):
        Recommendation.objects.filter(
            assessment__inspection__planting_attempt__field__farm__owner=self.user
        ).delete()

        self.client.force_login(self.user)

        response = self.client.get(reverse("recommendations:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No recommendations yet")

    def test_status_filter_works(self):
        self.recommendation.status = Recommendation.Status.COMPLETED
        self.recommendation.completed_at = timezone.now()
        self.recommendation.save()

        self.client.force_login(self.user)

        response = self.client.get(
            reverse("recommendations:list"),
            {"status": Recommendation.Status.COMPLETED},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.recommendation.title)

    def test_priority_filter_works(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("recommendations:list"),
            {"priority": Recommendation.Priority.HIGH},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.recommendation.title)

    def test_search_filter_works(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("recommendations:list"),
            {"q": "dry soil"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.recommendation.title)


class RecommendationDetailTests(RecommendationTestMixin, TestCase):

    def setUp(self):
        self.user = self.create_user("farmer")
        self.other_user = self.create_user("other")

        self.recommendation = self.create_recommendation(self.user)
        self.other_recommendation = self.create_recommendation(
            self.other_user,
            code="other_soil_dry",
        )

    def test_authenticated_user_can_view_own_recommendation(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "recommendations:detail",
                kwargs={"pk": self.recommendation.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.recommendation.title)
        self.assertContains(response, "Recommended action")
        self.assertContains(response, "Supporting Evidence")

    def test_user_cannot_view_another_users_recommendation(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "recommendations:detail",
                kwargs={"pk": self.other_recommendation.pk},
            )
        )

        self.assertEqual(response.status_code, 404)


class RecommendationUpdateTests(RecommendationTestMixin, TestCase):

    def setUp(self):
        self.user = self.create_user("farmer")
        self.other_user = self.create_user("other")

        self.recommendation = self.create_recommendation(self.user)
        self.other_recommendation = self.create_recommendation(
            self.other_user,
            code="other_soil_dry",
        )

    def test_user_can_update_status_and_follow_up_date(self):
        self.client.force_login(self.user)

        follow_up = date.today() + timedelta(days=7)

        response = self.client.post(
            reverse(
                "recommendations:update",
                kwargs={"pk": self.recommendation.pk},
            ),
            {
                "status": Recommendation.Status.IN_PROGRESS,
                "follow_up_date": follow_up.isoformat(),
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "recommendations:detail",
                kwargs={"pk": self.recommendation.pk},
            ),
        )

        self.recommendation.refresh_from_db()

        self.assertEqual(
            self.recommendation.status,
            Recommendation.Status.IN_PROGRESS,
        )
        self.assertEqual(
            self.recommendation.follow_up_date,
            follow_up,
        )
        self.assertIsNone(self.recommendation.completed_at)

    def test_marking_recommendation_completed_sets_completed_at(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "recommendations:update",
                kwargs={"pk": self.recommendation.pk},
            ),
            {
                "status": Recommendation.Status.COMPLETED,
                "follow_up_date": "",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "recommendations:detail",
                kwargs={"pk": self.recommendation.pk},
            ),
        )

        self.recommendation.refresh_from_db()

        self.assertEqual(
            self.recommendation.status,
            Recommendation.Status.COMPLETED,
        )
        self.assertIsNotNone(self.recommendation.completed_at)

    def test_moving_out_of_completed_clears_completed_at(self):
        self.recommendation.status = Recommendation.Status.COMPLETED
        self.recommendation.completed_at = timezone.now()
        self.recommendation.save()

        self.client.force_login(self.user)

        self.client.post(
            reverse(
                "recommendations:update",
                kwargs={"pk": self.recommendation.pk},
            ),
            {
                "status": Recommendation.Status.IN_PROGRESS,
                "follow_up_date": "",
            },
        )

        self.recommendation.refresh_from_db()

        self.assertEqual(
            self.recommendation.status,
            Recommendation.Status.IN_PROGRESS,
        )
        self.assertIsNone(self.recommendation.completed_at)

    def test_user_cannot_update_another_users_recommendation(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "recommendations:update",
                kwargs={"pk": self.other_recommendation.pk},
            ),
            {
                "status": Recommendation.Status.COMPLETED,
                "follow_up_date": "",
            },
        )

        self.assertEqual(response.status_code, 404)

        self.other_recommendation.refresh_from_db()

        self.assertEqual(
            self.other_recommendation.status,
            Recommendation.Status.PENDING,
        )
        self.assertIsNone(self.other_recommendation.completed_at)
