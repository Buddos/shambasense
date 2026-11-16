from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class FarmerRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Email address",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "you@example.com",
            "autocomplete": "email",
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["password1"].help_text = (
            "Your password should be at least 8 characters"
        )

        self.fields["password1"].widget.attrs.update({
            "class": "form-control",
            "autocomplete": "new-password",
            "placeholder": "Create a strong password",
        })

        self.fields["password2"].widget.attrs.update({
            "class": "form-control",
            "autocomplete": "new-password",
            "placeholder": "Enter your password again",
        })
        
    first_name = forms.CharField(
        required=True,
        label="First name",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Your first name",
            "autocomplete": "given-name",
        }),
    )

    last_name = forms.CharField(
        required=True,
        label="Last name",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Your last name",
            "autocomplete": "family-name",
        }),
    )

    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Choose a username",
            "autocomplete": "username",
        }),
    )

    phone_number = forms.CharField(
        required=False,
        label="Phone number",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "e.g. 0712345678",
            "autocomplete": "tel",
        }),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
        )
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email address already exists."
            )

        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number", "").strip()
        return phone or None

    def save(self, commit=True):
        user = super().save(commit=False)

        user.email = self.cleaned_data["email"]
        user.phone_number = self.cleaned_data.get("phone_number") or None

        # Public registration is restricted to farmer accounts.
        user.role = User.Role.FARMER
        user.is_staff = False
        user.is_superuser = False
        user.is_active = True

        if commit:
            user.save()

        return user