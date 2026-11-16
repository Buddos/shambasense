
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class PlantingAttempt(models.Model):
    class PlantingMethod(models.TextChoices):
        ROW = "row", "Row planting"
        HOLE = "hole", "Hole planting"
        BROADCAST = "broadcast", "Broadcast"
        TRANSPLANTING = "transplanting", "Transplanting"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        ABANDONED = "abandoned", "Abandoned"
        REPLACED = "replaced", "Replaced"

    field = models.ForeignKey(
        "farms.Field",
        on_delete=models.PROTECT,
        related_name="planting_attempts",
    )

    crop = models.ForeignKey(
        "crops.Crop",
        on_delete=models.PROTECT,
        related_name="planting_attempts",
    )

    variety = models.ForeignKey(
        "crops.Variety",
        on_delete=models.PROTECT,
        related_name="planting_attempts",
    )

    planting_date = models.DateField()

    expected_season_end_date = models.DateField(
        null=True,
        blank=True,
        help_text=(
            "Optional expected end date of the current growing season. "
            "Used to assess whether the variety's maturity window fits."
        ),
    )

    area_planted = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Area planted in acres.",
    )

    seed_source = models.CharField(
        max_length=150,
        blank=True,
        help_text="Where the farmer obtained the seed.",
    )

    planting_method = models.CharField(
        max_length=20,
        choices=PlantingMethod.choices,
        default=PlantingMethod.ROW,
    )

    target_plant_population_per_acre = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Farmer's intended plant population per acre, if known.",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-planting_date", "-created_at"]

    def clean(self):
        errors = {}

        if self.field_id and self.area_planted:
            if self.area_planted > self.field.acreage:
                errors["area_planted"] = (
                    f"Area planted ({self.area_planted} acres) cannot exceed "
                    f"the field size ({self.field.acreage} acres)."
                )

        if self.crop_id and self.variety_id:
            if self.variety.crop_id != self.crop_id:
                errors["variety"] = (
                    "The selected variety does not belong to the selected crop."
                )

        if self.planting_date and self.planting_date > timezone.localdate():
            errors["planting_date"] = "Planting date cannot be in the future."

        if (
            self.planting_date
            and self.expected_season_end_date
            and self.expected_season_end_date < self.planting_date
        ):
            errors["expected_season_end_date"] = (
                "Expected season end date cannot be before the planting date."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.crop.name} - {self.variety.name} - "
            f"{self.field.farm.name}/{self.field.name}"
        )