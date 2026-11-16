import logging

from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib import messages

from .forms import ContactForm


logger = logging.getLogger(__name__)


def home(request):
    return render(request, "public/home.html")


def about(request):
    return render(request, "public/about.html")


def privacy(request):
    return render(
        request,
        "public/privacy.html",
        {"contact_email": settings.CONTACT_EMAIL},
    )


def terms(request):
    return render(
        request,
        "public/terms.html",
        {"contact_email": settings.CONTACT_EMAIL},
    )


def contact(request):
    form = ContactForm(
        request.POST if request.method == "POST" else None
    )
    context = {
        "form": form,
        "contact_email": settings.CONTACT_EMAIL,
    }

    if request.method == "POST" and form.is_valid():
        recipient = settings.CONTACT_EMAIL
        if not recipient:
            messages.error(
                request,
                "The contact service is not configured yet. Please try again later.",
            )
            return render(request, "public/contact.html", context)

        subject = f"ShambaSense contact: {form.cleaned_data['subject']}"
        body = (
            f"Name: {form.cleaned_data['full_name']}\n"
            f"Email: {form.cleaned_data['email']}\n\n"
            f"{form.cleaned_data['message']}"
        )

        try:
            sent_count = send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL or recipient,
                [recipient],
                fail_silently=False,
                reply_to=[form.cleaned_data["email"]],
            )
        except Exception:
            logger.exception("Unable to deliver the public contact message")
            sent_count = 0

        if sent_count:
            messages.success(
                request,
                "Your message has been sent. Thank you for getting in touch.",
            )
            return redirect(reverse("pages:contact"))

        messages.error(
            request,
            "We could not send your message right now. Please try again later.",
        )

    return render(request, "public/contact.html", context)
