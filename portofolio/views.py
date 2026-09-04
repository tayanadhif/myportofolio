from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import render


MAX_ATTACHMENT_SIZE = 5 * 1024 * 1024


def landing_page(request):
    submitted = False
    email_error = False
    attachment_error = False

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        email = (request.POST.get("email") or "").strip()
        message = (request.POST.get("message") or "").strip()
        attachment = request.FILES.get("attachment")

        if name and email and message:
            if attachment and attachment.size > MAX_ATTACHMENT_SIZE:
                attachment_error = True
            else:
                try:
                    email_message = EmailMessage(
                    subject=f"Portfolio inquiry from {name}",
                        body=(
                        f"Name: {name}\n"
                        f"Email: {email}\n\n"
                        f"Message:\n{message}"
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