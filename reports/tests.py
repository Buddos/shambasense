from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from farms.models import Farm, Field
from crops.models import Crop, Variety
from planting.models import PlantingAttempt
from inspections.models import Inspection
from decision_engine.models import (
    EstablishmentAssessment,
    RemainingSeasonAssessment,
)
from recommendations.models import Recommendation


class ReportsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        today = timezone.localdate()

        # Farmer who owns the test records.
        cls.farmer = User.objects.create_user(
            username="report-farmer",
            email="farmer@example.com",
            password="test-password-123",
            role="farmer",
        )

        # A different farmer for access-control tests.
        cls.other_farmer = User.objects.create_user(
            username="other-farmer",
            email="other@example.com",
            password="test-password-123",
            role="farmer",
        )

        cls.farm = Farm.objects.create(
            owner=cls.farmer,
            name="Test Farm",
            county="Nakuru",
            sub_county="Njoro",
            total_acreage=Decimal("2.00"),
        )

        cls.field = Field.objects.create(
            farm=cls.farm,
            name="Field A",
            acreage=Decimal("1.00"),
            soil_type="Loam",
        )

        cls.crop = Crop.objects.create(
            name="Test Maize",
        )

        cls.variety = Variety.objects.create(
            crop=cls.crop,
            name="Test Hybrid",
            maturity_days_min=90,
            maturity_days_max=120,
        )

        cls.planting = PlantingAttempt.objects.create(
            field=cls.field,
            crop=cls.crop,
            variety=cls.variety,
            planting_date=today - timedelta(days=30),
            expected_season_end_date=today + timedelta(days=150),
            area_planted=Decimal("0.50"),
            planting_method="row",
            status="active",
            seed_source="Certified seed",
        )

        cls.inspection = Inspection.objects.create(
            planting_attempt=cls.planting,
            inspected_by=cls.farmer,
            inspection_date=today,
            crop_stage="seedling",
            planting_stations_observed=10,
            stations_with_emergence=8,
            healthy_plant_count=8,
            damaged_plant_count=0,
            crop_condition="good",
            soil_moisture="adequate",
            weed_pressure="low",
            pest_or_disease_signs=False,
            observations="Test inspection observations.",
            actions_taken="Routine monitoring.",
        )

        cls.establishment = EstablishmentAssessment.objects.create(
            inspection=cls.inspection,
            status="no_major_warning_signs",
            emergence_percentage=Decimal("80.00"),
            healthy_plant_count=8,
            damaged_plant_count=0,
            findings=["Emergence recorded in most observed stations."],
            summary="No major warning signs were recorded.",
            rule_version="1.0",
        )

        cls.season_assessment = RemainingSeasonAssessment.objects.create(
            planting_attempt=cls.planting,
            latest_inspection=cls.inspection,
            status="within_maturity_window",
            assessment_date=today,
            expected_maturity_start=(
                self_date := today + timedelta(days=60)
            ),
            expected_maturity_end=today + timedelta(days=90),
            expected_season_end_date=today + timedelta(days=150),
            days_after_planting=30,
            summary="The expected maturity window falls within the recorded season.",
            evidence={"test": True},
            rule_version="1.0",
        )

        cls.recommendation = Recommendation.objects.create(
            assessment=cls.establishment,
            code="test_monitoring",
            category="general",
            title="Continue field monitoring",
            explanation="Routine monitoring is appropriate.",
            recommended_action="Inspect the field again as scheduled.",
            priority="high",
            status="pending",
            is_active=True,
            evidence={"source": "test"},
            rule_version="1.0",
        )

    def login_as_owner(self):
        self.client.force_login(self.farmer)

    def test_reports_dashboard_requires_login(self):
        response = self.client.get(reverse("reports:dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_reports_dashboard_displays_owner_summary(self):
        self.login_as_owner()

        response = self.client.get(reverse("reports:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/dashboard.html")
        self.assertEqual(response.context["summary"]["farm_count"], 1)
        self.assertEqual(response.context["summary"]["field_count"], 1)
        self.assertEqual(response.context["summary"]["planting_count"], 1)
        self.assertEqual(response.context["summary"]["inspection_count"], 1)
        self.assertEqual(response.context["summary"]["establishment_count"], 1)
        self.assertEqual(response.context["summary"]["season_assessment_count"], 1)
        self.assertEqual(response.context["summary"]["active_recommendation_count"], 1)
        self.assertEqual(response.context["summary"]["high_priority_count"], 1)

    def test_reports_dashboard_does_not_include_another_farmers_records(self):
        other_farm = Farm.objects.create(
            owner=self.other_farmer,
            name="Other Farmer Farm",
            county="Kiambu",
            total_acreage=Decimal("3.00"),
        )

        self.login_as_owner()
        response = self.client.get(reverse("reports:dashboard"))

        self.assertEqual(response.status_code, 200)
        farm_ids = list(response.context["farms"].values_list("id", flat=True))
        self.assertNotIn(other_farm.id, farm_ids)
        self.assertEqual(response.context["summary"]["farm_count"], 1)

    def test_owner_can_view_all_html_reports(self):
        self.login_as_owner()

        report_urls = [
            ("reports:farm_detail", self.farm.pk),
            ("reports:planting_detail", self.planting.pk),
            ("reports:inspection_detail", self.inspection.pk),
            ("reports:assessment_detail", self.planting.pk),
            ("reports:recommendation_detail", self.recommendation.pk),
        ]

        for route_name, object_id in report_urls:
            with self.subTest(route=route_name):
                response = self.client.get(
                    reverse(route_name, args=[object_id])
                )
                self.assertEqual(response.status_code, 200)

    def test_other_farmer_cannot_view_html_reports(self):
        self.client.force_login(self.other_farmer)

        report_urls = [
            ("reports:farm_detail", self.farm.pk),
            ("reports:planting_detail", self.planting.pk),
            ("reports:inspection_detail", self.inspection.pk),
            ("reports:assessment_detail", self.planting.pk),
            ("reports:recommendation_detail", self.recommendation.pk),
        ]

        for route_name, object_id in report_urls:
            with self.subTest(route=route_name):
                response = self.client.get(
                    reverse(route_name, args=[object_id])
                )
                self.assertEqual(response.status_code, 404)

    def test_owner_can_download_all_pdf_reports(self):
        self.login_as_owner()

        pdf_urls = [
            ("reports:farm_pdf", self.farm.pk),
            ("reports:planting_pdf", self.planting.pk),
            ("reports:inspection_pdf", self.inspection.pk),
            ("reports:assessment_pdf", self.planting.pk),
            ("reports:recommendation_pdf", self.recommendation.pk),
        ]

        for route_name, object_id in pdf_urls:
            with self.subTest(route=route_name):
                response = self.client.get(
                    reverse(route_name, args=[object_id])
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response["Content-Type"], "application/pdf")
                self.assertTrue(response.content.startswith(b"%PDF-"))
                self.assertIn(
                    "attachment",
                    response["Content-Disposition"].lower(),
                )

    def test_other_farmer_cannot_download_another_farmers_pdfs(self):
        self.client.force_login(self.other_farmer)

        pdf_urls = [
            ("reports:farm_pdf", self.farm.pk),
            ("reports:planting_pdf", self.planting.pk),
            ("reports:inspection_pdf", self.inspection.pk),
            ("reports:assessment_pdf", self.planting.pk),
            ("reports:recommendation_pdf", self.recommendation.pk),
        ]

        for route_name, object_id in pdf_urls:
            with self.subTest(route=route_name):
                response = self.client.get(
                    reverse(route_name, args=[object_id])
                )
                self.assertEqual(response.status_code, 404)

    def test_farmer_with_no_records_sees_empty_reports_dashboard(self):
        self.client.force_login(self.other_farmer)

        response = self.client.get(reverse("reports:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["summary"]["farm_count"], 0)
        self.assertEqual(response.context["summary"]["planting_count"], 0)
        self.assertEqual(response.context["summary"]["inspection_count"], 0)
