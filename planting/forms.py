from django import forms

from .models import PlantingAttempt
from farms.models import Field
from crops.models import Crop, Variety


class PlantingAttemptForm(forms.ModelForm):
    class Meta:
        model = PlantingAttempt
        fields = (
            "field",
            "crop",
            "variety",
            "planting_date",
            "expected_season_end_date",
            "area_planted",
            "seed_source",
            "planting_method",
            "target_plant_population_per_acre",
            "status",
            "notes",
        )

        widgets = {
            "field": forms.Select(
                attrs={"class": "form-control"}
            ),
            "crop": forms.Select(
                attrs={"class": "form-control", "id": "id_crop"}
            ),
            "variety": forms.Select(
                attrs={"class": "form-control", "id": "id_variety"}
            ),
            "planting_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "expected_season_end_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "area_planted": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
            "seed_source": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Certified seed dealer",
                }
            ),
            "planting_method": forms.Select(
                attrs={"class": "form-control"}
            ),
            "target_plant_population_per_acre": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                }
            ),
            "status": forms.Select(
                attrs={"class": "form-control"}
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Any important information about this planting...",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.user = user

        if user and user.is_authenticated:
            self.fields["field"].queryset = (
                Field.objects
                .filter(farm__owner=user)
                .select_related("farm")
                .order_by("farm__name", "name")
            )
        else:
            self.fields["field"].queryset = Field.objects.none()

        self.fields["crop"].queryset = (
            Crop.objects
            .filter(is_active=True)
            .order_by("name")
        )

        self.fields["variety"].queryset = (
            Variety.objects
            .filter(is_active=True)
            .select_related("crop")
            .order_by("crop__name", "name")
        )

        self.fields["field"].label_from_instance = (
            lambda obj: f"{obj.farm.name} — {obj.name} ({obj.acreage} acres)"
        )

    def clean(self):
        cleaned_data = super().clean()

        field = cleaned_data.get("field")
        crop = cleaned_data.get("crop")
        variety = cleaned_data.get("variety")
        area_planted = cleaned_data.get("area_planted")

        if field and area_planted:
            if area_planted > field.acreage:
                self.add_error(
                    "area_planted",
                    f"Area planted cannot exceed the field size of "
                    f"{field.acreage} acres.",
                )

        if crop and variety:
            if variety.crop_id != crop.id:
                self.add_error(
                    "variety",
                    "The selected variety does not belong to the selected crop.",
                )

        return cleaned_data
