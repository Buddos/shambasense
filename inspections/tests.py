from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from crops.models import Crop, Variety
from farms.models import Farm, Field
from planting.models import PlantingAttempt
from inspections.models import Inspection
from inspections.forms import InspectionForm

from decision_engine.models import EstablishmentAssessment
from decision_engine.services import assess_establishment


class InspectionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="inspection_farmer",
            email="inspection@example.com",
            password="TestPassword123!",
        )

        self.farm = Farm.objects.create(
            owner=self.user,
            name="Test Farm",
            county="Nakuru",
            total_acreage=Decimal("5.00"),
        )

        self.field = Field.objects.create(
            farm=self.farm,
            name="Field A",
            acreage=Decimal("2.00"),
        )

        self.crop = Crop.objects.create(
            name="Maize",
        )

        self.variety = Variety.objects.create(
            crop=self.crop,
            name="H614",
            maturity_days_min=120,
            maturity_days_max=150,
        )

        self.planting = PlantingAttempt.objects.create(
            field=self.field,
            crop=self.crop,
            variety=self.variety,
            planting_date=timezone.localdate() - timedelta(days=10),
            area_planted=Decimal("1.00"),
        )

        self.inspection = Inspection.objects.create(
            planting_attempt=self.planting,
            inspection_date=timezone.localdate(),
            inspected_by=self.user,
            crop_stage="seedling",
            planting_stations_observed=20,
            stations_with_emergence=16,
            healthy_plant_count=16,
            damaged_plant_count=2,
            crop_condition="good",
            soil_moisture="adequate",
            weed_pressure="none",
            pest_or_disease_signs=False,
            observations="Normal crop development.",
            actions_taken="Routine monitoring.",
        )

    def test_emergence_percentage_is_calculated_correctly(self):
        self.assertAlmostEqual(
            float(self.inspection.emergence_percentage),
            80.0,
        )

    def test_emergence_percentage_returns_none_without_observations(self):
        inspection = Inspection(
            planting_attempt=self.planting,
            inspection_date=timezone.localdate(),
            crop_stage="seedling",
            planting_stations_observed=0,
            stations_with_emergence=0,
            healthy_plant_count=0,
            damaged_plant_count=0,
            crop_condition="good",
            soil_moisture="adequate",
            weed_pressure="none",
        )

        self.assertIsNone(inspection.emergence_percentage)

    def test_days_after_planting_is_calculated_correctly(self):
        self.assertEqual(
            self.inspection.days_after_planting,
            10,
        )

    def test_emergence_cannot_exceed_observed_stations(self):
        inspection = Inspection(
            planting_attempt=self.planting,
            inspection_date=timezone.localdate(),
            crop_stage="seedling",
            planting_stations_observed=10,
            stations_with_emergence=12,
            healthy_plant_count=12,
            damaged_plant_count=0,
            crop_condition="good",
            soil_moisture="adequate",
            weed_pressure="none",
        )

        with self.assertRaises(ValidationError):
            inspection.full_clean()

    def test_inspection_date_cannot_precede_planting_date(self):
        inspection = Inspection(
            planting_attempt=self.planting,
            inspection_date=(
                self.planting.planting_date - timedelta(days=1)
            ),
            crop_stage="seedling",
            planting_stations_observed=10,
            stations_with_emergence=5,
            healthy_plant_count=5,
            damaged_plant_count=0,
            crop_condition="good",
            soil_moisture="adequate",
            weed_pressure="none",
        )

        with self.assertRaises(ValidationError):
            inspection.full_clean()


class InspectionViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="farmer1",
            email="farmer1@example.com",
            password="TestPassword123!",
        )

        self.other_user = User.objects.create_user(
            username="farmer2",
            email="farmer2@example.com",
            password="TestPassword123!",
        )

        self.farm = Farm.objects.create(
            owner=self.user,
            name="Farmer One Farm",
            county="Nakuru",
            total_acreage=Decimal("5.00"),
        )

        self.other_farm = Farm.objects.create(
            owner=self.other_user,
            name="Farmer Two Farm",
            county="Nakuru",
            total_acreage=Decimal("4.00"),
        )

        self.field = Field.objects.create(
            farm=self.farm,
            name="North Field",
            acreage=Decimal("2.00"),
        )

        self.other_field = Field.objects.create(
            farm=self.other_farm,
            name="South Field",
            acreage=Decimal("1.50"),
        )

        self.crop = Crop.objects.create(
            name="Maize",
        )

        self.variety = Variety.objects.create(
            crop=self.crop,
            name="H614",
            maturity_days_min=120,
            maturity_days_max=150,
        )

        self.planting = PlantingAttempt.objects.create(
            field=self.field,
            crop=self.crop,
            variety=self.variety,
            planting_date=timezone.localdate() - timedelta(days=10),
            area_planted=Decimal("1.00"),
        )

        self.other_planting = PlantingAttempt.objects.create(
            field=self.other_field,
            crop=self.crop,
            variety=self.variety,
            planting_date=timezone.localdate() - timedelta(days=10),
            area_planted=Decimal("1.00"),
        )

        self.inspection = Inspection.objects.create(
            planting_attempt=self.planting,
            inspection_date=timezone.localdate(),
            inspected_by=self.user,
            crop_stage="seedling",
            planting_stations_observed=20,
            stations_with_emergence=16,
            healthy_plant_count=16,
            damaged_plant_count=2,
            crop_condition="good",
            soil_moisture="adequate",
            weed_pressure="none",
            pest_or_disease_signs=False,
            observations="Normal crop development.",
            actions_taken="Routine monitoring.",
        )

        self.client.force_login(self.user)

    def test_inspection_list_page_loads(self):
        response = self.client.get(
            reverse("inspections:list")
        )

        self.assertEqual(response.status_code, 200)

    def test_inspection_detail_page_loads(self):
        response = self.client.get(
            reverse(
                "inspections:detail",
                kwargs={"pk": self.inspection.pk},
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_inspection_create_page_loads(self):
        response = self.client.get(
            reverse("inspections:create")
        )

        self.assertEqual(response.status_code, 200)

    def test_farmer_sees_only_own_inspections(self):
        other_inspection = Inspection.objects.create(
            planting_attempt=self.other_planting,
            inspection_date=timezone.localdate(),
            inspected_by=self.other_user,
            crop_stage="seedling",
            planting_stations_observed=10,
            stations_with_emergence=5,
            healthy_plant_count=5,
            damaged_plant_count=0,
            crop_condition="good",
            soil_moisture="adequate",
            weed_pressure="none",
            pest_or_disease_signs=False,
        )

        response = self.client.get(reverse("inspections:list"))

        self.assertEqual(response.status_code, 200)

        # The farmer's own inspection should be visible.
        self.assertContains(response, self.crop.name)
        self.assertContains(response, self.farm.name)
        self.assertContains(response, self.field.name)

        # Another farmer's farm and field must not be visible.
        self.assertNotContains(response, self.other_farm.name)
        self.assertNotContains(response, self.other_field.name)

        self.assertTrue(
            Inspection.objects.filter(pk=other_inspection.pk).exists()
        )


    def test_farmer_cannot_view_another_farmers_inspection(self):
        other_inspection = Inspection.objects.create(
            planting_attempt=self.other_planting,
            inspection_date=timezone.localdate(),
            inspected_by=self.other_user,
            crop_stage="seedling",
            planting_stations_observed=10,
            stations_with_emergence=5,
            healthy_plant_count=5,
            damaged_plant_count=0,
            crop_condition="good",
            soil_moisture="adequate",
            weed_pressure="none",
        )

        response = self.client.get(
            reverse(
                "inspections:detail",
                kwargs={"pk": other_inspection.pk},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_farmer_cannot_update_another_farmers_inspection(self):
        other_inspection = Inspection.objects.create(
            planting_attempt=self.other_planting,
            inspection_date=timezone.localdate(),
            inspected_by=self.other_user,
            crop_stage="seedling",
            planting_stations_observed=10,
            stations_with_emergence=5,
            healthy_plant_count=5,
            damaged_plant_count=0,
            crop_condition="good",
            soil_moisture="adequate",
            weed_pressure="none",
        )

        response = self.client.get(
            reverse(
                "inspections:update",
                kwargs={"pk": other_inspection.pk},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_farmer_cannot_delete_another_farmers_inspection(self):
        other_inspection = Inspection.objects.create(
            planting_attempt=self.other_planting,
            inspection_date=timezone.localdate(),
            inspected_by=self.other_user,
            crop_stage="seedling",
            planting_stations_observed=10,
            stations_with_emergence=5,
            healthy_plant_count=5,
            damaged_plant_count=0,
            crop_condition="good",
            soil_moisture="adequate",
            weed_pressure="none",
        )

        response = self.client.post(
            reverse(
                "inspections:delete",
                kwargs={"pk": other_inspection.pk},
            )
        )

        self.assertEqual(response.status_code, 404)

        self.assertTrue(
            Inspection.objects.filter(
                pk=other_inspection.pk
            ).exists()
        )

    def test_inspection_form_only_shows_own_planting_attempts(self):
        form = InspectionForm(user=self.user)

        queryset = form.fields["planting_attempt"].queryset

        self.assertIn(
            self.planting,
            queryset,
        )

        self.assertNotIn(
            self.other_planting,
            queryset,
        )

    def test_farmer_can_create_inspection(self):
        response = self.client.post(
            reverse("inspections:create"),
            {
                "planting_attempt": self.planting.pk,
                "inspection_date": timezone.localdate().isoformat(),
                "crop_stage": "seedling",
                "planting_stations_observed": 20,
                "stations_with_emergence": 15,
                "healthy_plant_count": 15,
                "damaged_plant_count": 1,
                "crop_condition": "good",
                "soil_moisture": "adequate",
                "weed_pressure": "none",
                "pest_or_disease_signs": "",
                "observations": "New inspection.",
                "actions_taken": "",
                "follow_up_date": "",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Inspection.objects.filter(
                planting_attempt=self.planting,
                planting_stations_observed=20,
                stations_with_emergence=15,
            ).exists()
        )

    def test_farmer_can_delete_own_inspection(self):
        response = self.client.post(
            reverse(
                "inspections:delete",
                kwargs={"pk": self.inspection.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            Inspection.objects.filter(
                pk=self.inspection.pk
            ).exists()
        )

    def test_farmer_can_create_inspection_with_assessment(self):
        existing_ids = set(
            Inspection.objects.values_list("pk", flat=True)
        )

        response = self.client.post(
            reverse("inspections:create"),
            {
                "planting_attempt": self.planting.pk,
                "inspection_date": timezone.localdate().isoformat(),
                "crop_stage": "seedling",
                "planting_stations_observed": 20,
                "stations_with_emergence": 16,
                "healthy_plant_count": 16,
                "damaged_plant_count": 0,
                "crop_condition": "good",
                "soil_moisture": "adequate",
                "weed_pressure": "none",
                "pest_or_disease_signs": "",
                "observations": "Good crop establishment.",
                "actions_taken": "",
                "follow_up_date": "",
            },
        )

        self.assertEqual(response.status_code, 302)

        new_inspection = Inspection.objects.exclude(
            pk__in=existing_ids
        ).get()

        self.assertEqual(
            new_inspection.planting_attempt,
            self.planting,
        )

        self.assertTrue(
            EstablishmentAssessment.objects.filter(
                inspection=new_inspection,
            ).exists()
        )


    def test_updating_inspection_refreshes_assessment(self):
        assessment = assess_establishment(self.inspection)

        response = self.client.post(
            reverse(
                "inspections:update",
                kwargs={"pk": self.inspection.pk},
            ),
            {
                "planting_attempt": self.planting.pk,
                "inspection_date": timezone.localdate().isoformat(),
                "crop_stage": "seedling",
                "planting_stations_observed": 10,
                "stations_with_emergence": 8,
                "healthy_plant_count": 5,
                "damaged_plant_count": 6,
                "crop_condition": "poor",
                "soil_moisture": "adequate",
                "weed_pressure": "none",
                "pest_or_disease_signs": "",
                "observations": "Crop condition has deteriorated.",
                "actions_taken": "",
                "follow_up_date": "",
            },
        )

        self.assertEqual(response.status_code, 302)

        assessment.refresh_from_db()

        self.assertEqual(
            assessment.status,
            EstablishmentAssessment.Status.ATTENTION_REQUIRED,
        )

        self.assertEqual(
            assessment.healthy_plant_count,
            5,
        )

        self.assertEqual(
            assessment.damaged_plant_count,
            6,
        )

    def test_deleting_inspection_also_deletes_assessment(self):
        assessment = assess_establishment(self.inspection)
        assessment_id = assessment.pk

        response = self.client.post(
            reverse(
                "inspections:delete",
                kwargs={"pk": self.inspection.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            EstablishmentAssessment.objects.filter(
                pk=assessment_id
            ).exists()
        )
