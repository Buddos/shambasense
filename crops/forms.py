from django import forms

from .models import Crop, Variety


class CropForm(forms.ModelForm):
    class Meta:
        model = Crop
        fields = (
            "name",
            "scientific_name",
            "crop_type",
            "description",
            "is_active",
        )

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Maize",
            }),
            "scientific_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Zea mays",
            }),
            "crop_type": forms.Select(attrs={
                "class": "form-control",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Describe this crop...",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-checkbox",
            }),
        }


class VarietyForm(forms.ModelForm):
    class Meta:
        model = Variety
        fields = (
            "name",
            "maturity_days_min",
            "maturity_days_max",
            "description",
            "is_active",
        )

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. H614",
            }),
            "maturity_days_min": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1",
                "placeholder": "e.g. 120",
            }),
            "maturity_days_max": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1",
                "placeholder": "e.g. 150",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Describe this variety...",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-checkbox",
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        minimum = cleaned_data.get("maturity_days_min")
        maximum = cleaned_data.get("maturity_days_max")

        if minimum and maximum and minimum > maximum:
            raise forms.ValidationError(
                "Maximum maturity days must be greater than or equal to minimum maturity days."
            )

        return cleaned_data
