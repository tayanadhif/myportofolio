from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import render
from django.utils import timezone


MAX_ATTACHMENT_SIZE = 50 * 1024 * 1024


def landing_page(request):
    submitted = False
    email_error = False
    attachment_error = False

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        email = (request.POST.get("email") or "").strip()
        subject = (request.POST.get("subject") or "Portfolio contact form message").strip()
        message = (request.POST.get("message") or "").strip()
        attachment = request.FILES.get("attachment")

        if name and email and message:
            if settings.EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend":
                email_error = True
            elif attachment and attachment.size > MAX_ATTACHMENT_SIZE:
                attachment_error = True
            else:
                try:
                    email_message = EmailMessage(
                        subject=f"New Contact Form Message: {subject}",
                        body=(
                            f"New Contact Form Message: {subject}\n\n"
                            f"{timezone.localtime():%Y-%m-%d %H:%M:%S}\n\n"
                            f"Hello Nadhif Aydin Adinandra,\n\n"
                            "You got a new message from your portfolio website:\n\n"
                            f"From: {name}\n"
                            f"Email: {email}\n"
                            f"Subject: {subject}\n\n"
                            f"Message:\n{message}\n\n"
                            "This message was sent from your portfolio contact form.\n"
                            f"Reply directly to: {email}\n\n"
                            "Best wishes,\n"
                            "Cartoon Studio"
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[settings.RECEIVER_EMAIL],
                        reply_to=[email],
                    )
                    if attachment:
                        email_message.attach(
                            attachment.name,
                            attachment.read(),
                            attachment.content_type,
                        )
                    submitted = email_message.send(fail_silently=False) == 1
                    email_error = not submitted
                except (OSError, SMTPException):
                    email_error = True

    return render(
        request,
        "index.html",
        {
            "submitted": submitted,
            "email_error": email_error,
            "attachment_error": attachment_error,
        },
    )