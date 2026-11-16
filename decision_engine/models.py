from django.db import models


class EstablishmentAssessment(models.Model):

    class Status(models.TextChoices):
        LIMITED_DATA = (
            "limited_data",
            "Limited data",
        )

        NO_MAJOR_WARNING_SIGNS = (
            "no_major_warning_signs",
            "No major warning signs",
        )

        MIXED_SIGNALS = (
            "mixed_signals",
            "Mixed signals",
        )

        ATTENTION_REQUIRED = (
            "attention_required",
            "Attention required",
        )

    inspection = models.OneToOneField(
        "inspections.Inspection",
       on_delete=models.CASCADE,
        related_name="establishment_assessment",
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
    )

    emergence_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    healthy_plant_count = models.PositiveIntegerField(
        default=0,
    )

    damaged_plant_count = models.PositiveIntegerField(
        default=0,
    )

    findings = models.JSONField(
        default=list,
        blank=True,
    )

    summary = models.TextField()

    rule_version = models.CharField(
        max_length=20,
        default="1.0",
    )

    assessed_at = models.DateTimeField(
        auto_now=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-assessed_at"]

    def __str__(self):
        return (
            f"Establishment assessment — "
            f"{self.inspection.planting_attempt}"
        )
class RemainingSeasonAssessment(models.Model):

    class Status(models.TextChoices):
        INSUFFICIENT_DATA = (
            "insufficient_data",
            "Insufficient data",
        )
        WITHIN_MATURITY_WINDOW = (
            "within_maturity_window",
            "Within maturity window",
        )
        SEASON_CONSTRAINT = (
            "season_constraint",
            "Season constraint",
        )
        TIMING_UNCERTAIN = (
            "timing_uncertain",
            "Timing uncertain",
        )
        ATTENTION_REQUIRED = (
            "attention_required",
            "Attention required",
        )
        MATURITY_REACHED = (
            "maturity_reached",
            "Maturity reached",
        )
        MATURITY_WINDOW_ELAPSED = (
            "maturity_window_elapsed",
            "Expected maturity window elapsed",
        )

    planting_attempt = models.OneToOneField(
        "planting.PlantingAttempt",
        on_delete=models.CASCADE,
        related_name="remaining_season_assessment",
    )

    latest_inspection = models.ForeignKey(
        "inspections.Inspection",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="remaining_season_assessments",
    )

    status = models.CharField(
        max_length=35,
        choices=Status.choices,
    )

    assessment_date = models.DateField()

    expected_maturity_start = models.DateField(
        null=True,
        blank=True,
    )

    expected_maturity_end = models.DateField(
        null=True,
        blank=True,
    )

    expected_season_end_date = models.DateField(
        null=True,
        blank=True,
    )

    days_after_planting = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    summary = models.TextField()

    evidence = models.JSONField(
        default=dict,
        blank=True,
    )

    rule_version = models.CharField(
        max_length=20,
        default="1.0",
    )

    assessed_at = models.DateTimeField(auto_now=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-assessed_at"]
        verbose_name = "Remaining-season assessment"
        verbose_name_plural = "Remaining-season assessments"

    def __str__(self):
        return (
            f"Remaining-season assessment — "
            f"{self.planting_attempt}"
        )