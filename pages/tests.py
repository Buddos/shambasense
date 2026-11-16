from smtplib import SMTPException
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(
    ALLOWED_HOSTS=["testserver"],
    CONTACT_EMAIL="support@example.test",
    DEFAULT_FROM_EMAIL="no-reply@example.test",
)
class PublicPagesTests(TestCase):
    def test_public_pages_load_without_authentication(self):
        page_names = (
            "pages:home",
            "pages:about",
            "pages:privacy",
            "pages:terms",
            "pages:contact",
        )

        for name in page_names:
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)

    def test_home_actions_use_existing_account_routes(self):
        response = self.client.get(reverse("pages:home"))
        html = response.content.decode()
        navigation = html.split(
            '<nav class="public-nav" id="public-navigation"',
            1,
        )[1].split("</nav>", 1)[0]

        self.assertContains(
            response,
            f'href="{reverse("accounts:register")}"',
        )
        self.assertContains(
            response,
            f'href="{reverse("accounts:login")}"',
        )
        self.assertIn('class="hero-actions"', html)
        self.assertNotIn(reverse("accounts:login"), navigation)
        self.assertNotIn(reverse("accounts:register"), navigation)

    def test_dashboard_named_route_remains_authenticated(self):
        dashboard_url = reverse("dashboard:home")
        self.assertEqual(dashboard_url, "/dashboard/")

        response = self.client.get(dashboard_url)
        self.assertRedirects(
            response,
            f'{reverse("accounts:login")}?next={dashboard_url}',
        )

    def test_contact_rejects_invalid_submission_and_keeps_values(self):
        response = self.client.post(
            reverse("pages:contact"),
            {
                "full_name": "A Farmer",
                "email": "not-an-email",
                "subject": "Question",
                "message": "I have a question.",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a valid email address.")
        self.assertContains(response, 'value="A Farmer"')
        self.assertTrue(response.context["form"].errors)

    @patch("pages.views.send_mail", return_value=1)
    def test_contact_sends_valid_submission(self, send_mail_mock):
        response = self.client.post(
            reverse("pages:contact"),
            {
                "full_name": "A Farmer",
                "email": "farmer@example.test",
                "subject": "Help with my account",
                "message": "Please contact me.",
            },
        )

        self.assertRedirects(response, reverse("pages:contact"))
        send_mail_mock.assert_called_once()
        self.assertEqual(send_mail_mock.call_args.args[2], "no-reply@example.test")
        self.assertEqual(
            send_mail_mock.call_args.args[3],
            ["support@example.test"],
        )
        self.assertEqual(
            send_mail_mock.call_args.kwargs["reply_to"],
            ["farmer@example.test"],
        )

    @patch("pages.views.send_mail", side_effect=SMTPException("mail transport failed"))
    def test_contact_handles_email_delivery_failure(self, send_mail_mock):
        response = self.client.post(
            reverse("pages:contact"),
            {
                "full_name": "A Farmer",
                "email": "farmer@example.test",
                "subject": "Help",
                "message": "Please contact me.",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "We could not send your message right now.")
        self.assertNotContains(response, "mail transport failed")
        self.assertContains(response, 'value="A Farmer"')
        send_mail_mock.assert_called_once()

    @override_settings(CONTACT_EMAIL="")
    @patch("pages.views.send_mail")
    def test_contact_handles_missing_recipient_configuration(self, send_mail_mock):
        response = self.client.post(
            reverse("pages:contact"),
            {
                "full_name": "A Farmer",
                "email": "farmer@example.test",
                "subject": "Help",
                "message": "Please contact me.",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "contact service is not configured")
        send_mail_mock.assert_not_called()
