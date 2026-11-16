from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Farm(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="farms",
    )
    name = models.CharField(
        max_length=150,
        help_text="A name you use to identify this farm.",
    )
    county = models.CharField(max_length=100)
    sub_county = models.CharField(max_length=100, blank=True)
    ward = models.CharField(max_length=100, blank=True)
    village = models.CharField(max_length=100, blank=True)
    location_description = models.TextField(
        blank=True,
        help_text="Optional description of the farm's location.",
    )
    total_acreage = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Total farm size in acres.",
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name"],
                name="unique_farm_name_per_owner",
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.owner.username}"


class Field(models.Model):
    farm = models.ForeignKey(
        Farm,
        on_delete=models.CASCADE,
        related_name="fields",
    )
    name = models.CharField(
        max_length=100,
        help_text="Field name or identifier.",
    )
    acreage = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Field size in acres.",
    )
    soil_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional known soil type.",
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["farm", "name"],
                name="unique_field_name_per_farm",
            )
        ]

    def __str__(self):
        return f"{self.farm.name} - {self.name}"
