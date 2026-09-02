from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render


def landing_page(request):
    submitted = False

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        email = (request.POST.get("email") or "").strip()
        message = (request.POST.get("message") or "").strip()

        if name and email and message:
            send_mail(
                subject=f"Portfolio inquiry from {name}",
                message=(
                    f"Name: {name}\n"
                    f"Email: {email}\n\n"
                    f"Message:\n{message}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.RECEIVER_EMAIL],
                fail_silently=False,
            )
            submitted = True

    return render(request, "index.html", {"submitted": submitted})