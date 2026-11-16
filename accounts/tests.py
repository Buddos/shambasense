from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import FarmerRegistrationForm

User = get_user_model()


class FarmerRegistrationTests(TestCase):
    def setUp(self):
        self.registration_url = reverse("accounts:register")
        self.login_url = reverse("accounts:login")

    def valid_registration_data(self):
        return {
            "username": "testfarmer",
            "first_name": "John",
            "last_name": "Kamau",
            "email": "john@example.com",
            "phone_number": "0712345678",
            "password1": "SecureFarmPass!2026",
            "password2": "SecureFarmPass!2026",
        }

    def test_farmer_can_register(self):
        response = self.client.post(
            self.registration_url,
            self.valid_registration_data(),
        )

        self.assertRedirects(response, self.login_url)

        user = User.objects.get(username="testfarmer")

        self.assertEqual(user.email, "john@example.com")
        self.assertEqual(user.role, User.Role.FARMER)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_password_is_hashed(self):
        self.client.post(
            self.registration_url,
            self.valid_registration_data(),
        )

        user = User.objects.get(username="testfarmer")

        self.assertNotEqual(
            user.password,
            "SecureFarmPass!2026",
        )
        self.assertTrue(
            user.check_password("SecureFarmPass!2026")
        )

    def test_public_registration_cannot_assign_admin_role(self):
        data = self.valid_registration_data()
        data["role"] = User.Role.ADMINISTRATOR

        self.client.post(
            self.registration_url,
            data,
        )

        user = User.objects.get(username="testfarmer")

        self.assertEqual(
            user.role,
            User.Role.FARMER,
        )
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_duplicate_email_is_rejected_case_insensitively(self):
        User.objects.create_user(
            username="existingfarmer",
            email="john@example.com",
            password="AnotherSecurePass!2026",
        )

        data = self.valid_registration_data()
        data["email"] = "JOHN@EXAMPLE.COM"

        response = self.client.post(
            self.registration_url,
            data,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            User.objects.filter(
                username="testfarmer"
            ).exists()
        )

    def test_invalid_password_confirmation_is_rejected(self):
        data = self.valid_registration_data()
        data["password2"] = "DifferentPassword!2026"

        response = self.client.post(
            self.registration_url,
            data,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            User.objects.filter(
                username="testfarmer"
            ).exists()
        )

    def test_authenticated_user_cannot_register_again(self):
        user = User.objects.create_user(
            username="loggedinfarmer",
            email="loggedin@example.com",
            password="SecureFarmPass!2026",
        )

        self.client.force_login(user)

        response = self.client.get(
            self.registration_url
        )

        self.assertRedirects(
            response,
            reverse("accounts:profile"),
        )


class FarmerLoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="loginfarmer",
            email="login@example.com",
            password="SecureFarmPass!2026",
        )

    def test_farmer_can_log_in(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "loginfarmer",
                "password": "SecureFarmPass!2026",
            },
        )

        self.assertRedirects(
            response,
            reverse("dashboard:home"),
        )

    def test_wrong_password_is_rejected(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "loginfarmer",
                "password": "WrongPassword!2026",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            response.wsgi_request.user.is_authenticated
        )

    def test_login_and_registration_pages_link_back_home(self):
        home_url = reverse("pages:home")

        for page_url in (reverse("accounts:login"), reverse("accounts:register")):
            with self.subTest(page=page_url):
                response = self.client.get(page_url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, f'href="{home_url}"')

    def test_profile_requires_authentication(self):
        response = self.client.get(
            reverse("accounts:profile")
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("accounts:login"),
            response.url,
        )

    def test_logged_in_farmer_can_view_profile(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("accounts:profile")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "loginfarmer")
        self.assertContains(response, "login@example.com")

    def test_farmer_can_log_out(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:logout")
        )

        self.assertRedirects(
            response,
            reverse("accounts:login"),
        )

        profile_response = self.client.get(
            reverse("accounts:profile")
        )

        self.assertEqual(
            profile_response.status_code,
            302,
        )


class FarmerRegistrationFormTests(TestCase):
    def test_password_help_text_is_single_line(self):
        form = FarmerRegistrationForm()

        self.assertEqual(
            form.fields["password1"].help_text,
            "Your password should be at least 8 characters",
        )

    def test_registration_form_has_no_role_field(self):
        form = FarmerRegistrationForm()

        self.assertNotIn(
            "role",
            form.fields,
        )
        self.assertNotIn(
            "is_staff",
            form.fields,
        )
        self.assertNotIn(
            "is_superuser",
            form.fields,
        )
