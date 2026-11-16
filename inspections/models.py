from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Inspection(models.Model):

    class CropStage(models.TextChoices):
        EMERGENCE = "emergence", "Emergence"
        SEEDLING = "seedling", "Seedling"
        VEGETATIVE = "vegetative", "Vegetative"
        FLOWERING = "flowering", "Flowering"
        FRUITING = "fruiting", "Fruiting"
        MATURITY = "maturity", "Maturity"
        OTHER = "other", "Other"

    class CropCondition(models.TextChoices):
        EXCELLENT = "excellent", "Excellent"
        GOOD = "good", "Good"
        FAIR = "fair", "Fair"
        POOR = "poor", "Poor"

    class SoilMoisture(models.TextChoices):
        DRY = "dry", "Dry"
        LOW = "low", "Low"
        ADEQUATE = "adequate", "Adequate"
        WET = "wet", "Wet"
        WATERLOGGED = "waterlogged", "Waterlogged"

    class WeedPressure(models.TextChoices):
        NONE = "none", "None"
        LOW = "low", "Low"
        MODERATE = "moderate", "Moderate"
        HIGH = "high", "High"

    planting_attempt = models.ForeignKey(
        "planting.PlantingAttempt",
        on_delete=models.PROTECT,
        related_name="inspections",
    )

    inspected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="field_inspections",
    )

    inspection_date = models.DateField(
        default=timezone.localdate,
    )

    crop_stage = models.CharField(
        max_length=20,
        choices=CropStage.choices,
    )

    # Field sampling observations
    planting_stations_observed = models.PositiveIntegerField(
        default=0,
        help_text="Total planting stations examined during this inspection.",
    )

    stations_with_emergence = models.PositiveIntegerField(
        default=0,
        help_text="Number of examined stations where plants have emerged.",
    )

    healthy_plant_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of healthy plants observed in the sample.",
    )

    damaged_plant_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of damaged or visibly unhealthy plants observed.",
    )

    crop_condition = models.CharField(
        max_length=20,
        choices=CropCondition.choices,
    )

    soil_moisture = models.CharField(
        max_length=20,
        choices=SoilMoisture.choices,
    )

    weed_pressure = models.CharField(
        max_length=20,
        choices=WeedPressure.choices,
        default=WeedPressure.NONE,
    )

    pest_or_disease_signs = models.BooleanField(
        default=False,
        help_text="Whether visible signs of pests or disease were observed.",
    )

    observations = models.TextField(
        blank=True,
        help_text="Additional field observations.",
    )

    actions_taken = models.TextField(
        blank=True,
        help_text="Any field actions already taken by the farmer or inspector.",
    )

    follow_up_date = models.DateField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-inspection_date", "-created_at"]

    def clean(self):
        errors = {}

        if self.planting_attempt_id and self.inspection_date:
            planting_date = self.planting_attempt.planting_date

            if self.inspection_date < planting_date:
                errors["inspection_date"] = (
                    "Inspection date cannot be before the planting date."
                )

            if self.inspection_date > timezone.localdate():
                errors["inspection_date"] = (
                    "Inspection date cannot be in the future."
                )

        if self.planting_stations_observed is not None:
            if self.stations_with_emergence > self.planting_stations_observed:
                errors["stations_with_emergence"] = (
                    "Stations with emergence cannot exceed "
                    "the number of stations observed."
                )

        if (
            self.inspection_date
            and self.follow_up_date
            and self.follow_up_date < self.inspection_date
        ):
            errors["follow_up_date"] = (
                "Follow-up date cannot be before the inspection date."
            )

        if errors:
            raise ValidationError(errors)

    @property
    def emergence_percentage(self):
        if self.planting_stations_observed == 0:
            return None

        return round(
            (
                self.stations_with_emergence
                / self.planting_stations_observed
            ) * 100,
            2,
        )

    @property
    def days_after_planting(self):
        if not self.planting_attempt_id or not self.inspection_date:
            return None

        return (
            self.inspection_date
            - self.planting_attempt.planting_date
        ).days

    def __str__(self):
        return (
            f"Inspection: {self.planting_attempt} "
            f"on {self.inspection_date}"
        )
