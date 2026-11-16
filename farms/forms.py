from django import forms

from .models import Farm, Field


class FarmForm(forms.ModelForm):
    class Meta:
        model = Farm
        fields = (
            "name",
            "county",
            "sub_county",
            "ward",
            "village",
            "location_description",
            "total_acreage",
            "notes",
        )

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Mwongera Farm",
            }),
            "county": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Nakuru",
            }),
            "sub_county": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Njoro",
            }),
            "ward": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Mau Narok",
            }),
            "village": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Baraka",
            }),
            "location_description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Describe the farm location...",
            }),
            "total_acreage": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
                "placeholder": "e.g. 5.50",
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Additional farm notes...",
            }),
        }


class FieldForm(forms.ModelForm):
    class Meta:
        model = Field
        fields = (
            "name",
            "acreage",
            "soil_type",
            "notes",
        )

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Field A",
            }),
            "acreage": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
                "placeholder": "e.g. 1.25",
            }),
            "soil_type": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Loam",
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Additional field information...",
            }),
        }
