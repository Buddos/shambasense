from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Crop(models.Model):
    class CropType(models.TextChoices):
        CEREAL = "cereal", "Cereal"
        LEGUME = "legume", "Legume"
        VEGETABLE = "vegetable", "Vegetable"
        ROOT_TUBER = "root_tuber", "Root/Tuber"
        FRUIT = "fruit", "Fruit"
        CASH_CROP = "cash_crop", "Cash Crop"
        OTHER = "other", "Other"

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    scientific_name = models.CharField(
        max_length=150,
        blank=True,
    )

    crop_type = models.CharField(
        max_length=20,
        choices=CropType.choices,
        default=CropType.OTHER,
    )

    description = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Variety(models.Model):
    crop = models.ForeignKey(
        Crop,
        on_delete=models.CASCADE,
        related_name="varieties",
    )

    name = models.CharField(
        max_length=150,
    )

    maturity_days_min = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
        ],
        help_text="Minimum expected maturity period in days.",
    )

    maturity_days_max = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
        ],
        help_text="Maximum expected maturity period in days.",
    )

    description = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["crop", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["crop", "name"],
                name="unique_variety_name_per_crop",
            )
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if (
            self.maturity_days_min
            and self.maturity_days_max
            and self.maturity_days_min > self.maturity_days_max
        ):
            raise ValidationError({
                "maturity_days_max":
                    "Maximum maturity days must be greater than or equal to minimum maturity days."
            })

    def __str__(self):
        return f"{self.crop.name} - {self.name}"
