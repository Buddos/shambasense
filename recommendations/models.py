
from django.db import models


class Recommendation(models.Model):

    class Category(models.TextChoices):
        ESTABLISHMENT = "establishment", "Crop establishment"
        SEASON = "season", "Season timing"
        WATER = "water", "Water management"
        WEEDS = "weeds", "Weed management"
        CROP_HEALTH = "crop_health", "Crop health"
        PEST_DISEASE = "pest_disease", "Pest and disease investigation"
        SAMPLING = "sampling", "Field sampling"
        GENERAL = "general", "General guidance"

    class Priority(models.TextChoices):
        INFORMATIONAL = "informational", "Informational"
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        DISMISSED = "dismissed", "Dismissed"

    assessment = models.ForeignKey(
        "decision_engine.EstablishmentAssessment",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="recommendations",
    )

    remaining_season_assessment = models.ForeignKey(
        "decision_engine.RemainingSeasonAssessment",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="recommendations",
    )

    code = models.CharField(
        max_length=60,
    )

    occurrence = models.PositiveIntegerField(default=1)

    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.GENERAL,
    )

    title = models.CharField(
        max_length=180,
    )

    explanation = models.TextField(
        help_text="Why this recommendation was generated.",
    )

    recommended_action = models.TextField(
        help_text="The practical action suggested to the farmer.",
    )

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.INFORMATIONAL,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    is_active = models.BooleanField(
    default=True,
    help_text="Whether this recommendation is part of the current assessment guidance.",
    )
    
    evidence = models.JSONField(
        default=dict,
        blank=True,
        help_text="Inspection observations supporting this recommendation.",
    )

    rule_version = models.CharField(
        max_length=20,
        default="1.0",
    )

    follow_up_date = models.DateField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(assessment__isnull=False,
                             remaining_season_assessment__isnull=True)
                    | models.Q(assessment__isnull=True,
                              remaining_season_assessment__isnull=False)
                ),
                name="recommendation_has_one_source",
            ),
            models.CheckConstraint(
                condition=models.Q(occurrence__gte=1),
                name="recommendation_occurrence_positive",
            ),
            models.UniqueConstraint(
                fields=["assessment", "code", "occurrence"],
                name="unique_establishment_recommendation_occurrence",
            ),
            models.UniqueConstraint(
                fields=["remaining_season_assessment", "code", "occurrence"],
                name="unique_season_recommendation_occurrence",
            ),
        ]

        indexes = [
            models.Index(
                fields=["assessment", "status"],
                name="rec_assessment_status_idx",
            ),
            models.Index(
                fields=["remaining_season_assessment", "status"],
                name="rec_season_status_idx",
            ),
        ]

    @property
    def planting_attempt(self):
        if self.assessment_id:
            return self.assessment.inspection.planting_attempt
        return self.remaining_season_assessment.planting_attempt

    @property
    def source_inspection(self):
        if self.assessment_id:
            return self.assessment.inspection
        return self.remaining_season_assessment.latest_inspection

    @property
    def source_date(self):
        if self.assessment_id:
            return self.assessment.inspection.inspection_date
        return self.remaining_season_assessment.assessment_date

    @property
    def source_status(self):
        if self.assessment_id:
            return self.assessment.get_status_display()
        return self.remaining_season_assessment.get_status_display()

    @property
    def source_rule_version(self):
        if self.assessment_id:
            return self.assessment.rule_version
        return self.remaining_season_assessment.rule_version

    def __str__(self):
        return f"{self.title} - {self.planting_attempt}"
