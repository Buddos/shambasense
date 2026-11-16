from django import forms


class ContactForm(forms.Form):
    full_name = forms.CharField(
        label="Full name",
        max_length=120,
        widget=forms.TextInput(attrs={
            "autocomplete": "name",
            "class": "public-form-control",
        }),
    )
    email = forms.EmailField(
        label="Email address",
        max_length=254,
        widget=forms.EmailInput(attrs={
            "autocomplete": "email",
            "class": "public-form-control",
        }),
    )
    subject = forms.CharField(
        max_length=160,
        widget=forms.TextInput(attrs={
            "class": "public-form-control",
        }),
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "public-form-control",
            "rows": 6,
        }),
    )
