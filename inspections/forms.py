from django import forms

from planting.models import PlantingAttempt
from .models import Inspection


class InspectionForm(forms.ModelForm):
    class Meta:
        model = Inspection
        fields = (
            "planting_attempt",
            "inspection_date",
            "crop_stage",
            "planting_stations_observed",
            "stations_with_emergence",
            "healthy_plant_count",
            "damaged_plant_count",
            "crop_condition",
            "soil_moisture",
            "weed_pressure",
            "pest_or_disease_signs",
            "observations",
            "actions_taken",
            "follow_up_date",
        )

        widgets = {
            "planting_attempt": forms.Select(attrs={
                "class": "form-control",
            }),
            "inspection_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "crop_stage": forms.Select(attrs={
                "class": "form-control",
            }),
            "planting_stations_observed": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
            "stations_with_emergence": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
            "healthy_plant_count": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
            "damaged_plant_count": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
            }),
            "crop_condition": forms.Select(attrs={
                "class": "form-control",
            }),
            "soil_moisture": forms.Select(attrs={
                "class": "form-control",
            }),
            "weed_pressure": forms.Select(attrs={
                "class": "form-control",
            }),
            "pest_or_disease_signs": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
            "observations": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Describe what you observed in the field...",
            }),
            "actions_taken": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Describe any actions already taken...",
            }),
            "follow_up_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user and user.is_authenticated:
            self.fields["planting_attempt"].queryset = (
                PlantingAttempt.objects
                .filter(field__farm__owner=user)
                .select_related("field", "field__farm", "crop", "variety")
                .order_by("-planting_date")
            )
        else:
            self.fields["planting_attempt"].queryset = (
                PlantingAttempt.objects.none()
            )

        self.fields["planting_attempt"].label_from_instance = (
            lambda obj: (
                f"{obj.crop.name} ({obj.variety.name}) — "
                f"{obj.field.farm.name} / {obj.field.name}"
            )
        )

    def clean(self):
        cleaned_data = super().clean()

        observed = cleaned_data.get("planting_stations_observed")
        emerged = cleaned_data.get("stations_with_emergence")

        if observed is not None and emerged is not None:
            if emerged > observed:
                self.add_error(
                    "stations_with_emergence",
                    "Emergence count cannot exceed the number of "
                    "planting stations observed.",
                )

        return cleaned_data
