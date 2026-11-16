
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        FARMER = "farmer", "Farmer"
        AGRONOMIST = "agronomist", "Agronomist"
        ADMINISTRATOR = "administrator", "Administrator"

    email = models.EmailField(
        unique=True,
        help_text="User's email address"
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.FARMER
    )

    profile_picture = models.ImageField(
        upload_to="profile_photos/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_farmer(self):
        return self.role == self.Role.FARMER

    @property
    def is_agronomist(self):
        return self.role == self.Role.AGRONOMIST

    @property
    def is_administrator(self):
        return self.role == self.Role.ADMINISTRATOR
