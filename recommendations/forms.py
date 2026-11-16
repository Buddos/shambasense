from django import forms

from .models import Recommendation


class RecommendationUpdateForm(forms.ModelForm):
    """
    Farmers can update progress and schedule follow-ups.
    Generated recommendation content and evidence remain read-only.
    """

    class Meta:
        model = Recommendation
        fields = ["status", "follow_up_date"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
            "follow_up_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
        }
