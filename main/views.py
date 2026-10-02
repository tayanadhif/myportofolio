from functools import wraps
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.core import serializers
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.decorators.http import require_http_methods, require_POST

from main.forms import (
    AccountDetailsForm,
    PortfolioItemForm,
    ProjectForm,
    RegistrationForm,
    UserConnectionFormSet,
    UserProfileForm,
)
from main.models import ChatMessage, Experience, PortfolioItem, ProjectComment, UserProfile


EDITOR_REQUIRED_PERMISSIONS = (
    "main.add_portfolioitem",
    "main.change_portfolioitem",
    "main.delete_portfolioitem",
)

logger = logging.getLogger(__name__)


def user_has_editor_access(user):
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return user.has_perms(EDITOR_REQUIRED_PERMISSIONS)


def editor_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not user_has_editor_access(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def show_main(request):
    last_login = request.COOKIES.get("last_login")
    if not last_login:
        last_login = "Belum ada sesi login / Cookie tidak ditemukan"

    context = {
        "name": "Nadhif Aydin Adinandra",
        "npm": "2506537745",
        "study_program": "S1 Ilmu Komputer",
        "bio": (
            "Computer Science student at Universitas Indonesia interested in programming, mathematics, and game development. Outside of academics, I also create gaming content on YouTube, sharing gameplay, longplays, and other gaming projects. Feel free to check out my channel and see what I do beyond Fasilkom. I also enjoy exploring new technologies and staying up-to-date with the latest trends in the tech world. My passion for learning drives me to continuously improve my skills and contribute to exciting projects."
        ),
        "last_login": last_login,
        "logged_in_members": User.objects.exclude(last_login__isnull=True).order_by("-last_login"),
    }

    return render(request, "index.html", context)


def show_experience(request):
    experience_list = list(Experience.objects.all())

    if not experience_list:
        experience_list = [
            Experience(
                title="Computer Science Student",
                description="Building programming, problem-solving, and software development skills through coursework and personal projects.",
                category="full-time",
            ),
            Experience(
                title="Gaming Content Creator",
                description="Creating gameplay videos, longplays, and gaming projects while developing skills in editing and digital content production.",
                category="freelance",
            ),
            Experience(
                title="Math Teaching",
                description="Helping students understand mathematical concepts through clear explanations, examples, and problem-solving practice.",
                category="volunteer",
            ),
        ]

    context = {
        "name": "Nadhif Aydin Adinandra",
        "experience_list": experience_list,
    }

    return render(request, "experience.html", context)


def show_portfolio(request):
    context = {
        "name": "Nadhif Aydin Adinandra",
    }

    return render(request, "portfolio.html", context)


def get_portfolio_json(request):
    title_query = request.GET.get("title", "").strip()
    portfolio_items = PortfolioItem.objects.prefetch_related("starred_by").order_by("created_at")

    if title_query:
        portfolio_items = portfolio_items.filter(title__icontains=title_query)

    data = []
    for item in portfolio_items:
        starred_users = list(item.starred_by.all())
        data.append({
            "id": str(item.id),
            "title": item.title,
            "description": item.description,
            "category": item.category,
            "link": item.link,
            "star_count": len(starred_users),
            "is_starred": request.user.is_authenticated and request.user in starred_users,
        })

    return JsonResponse(data, safe=False)


def get_portfolio_xml(request):
    title_query = request.GET.get("title", "").strip()
    portfolio_items = PortfolioItem.objects.all()

    if title_query:
        portfolio_items = portfolio_items.filter(title__icontains=title_query)

    portfolio_items_xml = serializers.serialize("xml", portfolio_items)
    return HttpResponse(portfolio_items_xml, content_type="application/xml")


@login_required
@permission_required("main.add_portfolioitem", raise_exception=True)
def create_portfolio_item(request):
    form = PortfolioItemForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Portfolio baru berhasil ditambahkan!")
        return redirect("main:show_portfolio")

    context = {
        "name": "Nadhif Aydin Adinandra",
        "form": form,
        "form_action_url": "main:create_portfolio_item",
        "submit_button_text": "Tambah Portfolio",
    }

    return render(request, "portfolio_form.html", context)


@login_required
@editor_required
def update_portfolio_item(request, portfolio_id):
    portfolio_item = get_object_or_404(PortfolioItem, pk=portfolio_id)
    form = PortfolioItemForm(request.POST or None, instance=portfolio_item)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Portfolio berhasil diperbarui!")
        return redirect("main:show_portfolio")

    context = {
        "name": "Nadhif Aydin Adinandra",
        "form": form,
        "form_action_url": "main:update_portfolio_item",
        "submit_button_text": "Simpan Perubahan",
        "update_object": portfolio_item,
    }

    return render(request, "portfolio_form.html", context)


@login_required
@editor_required
def delete_portfolio_item(request, portfolio_id):
    portfolio_item = get_object_or_404(PortfolioItem, pk=portfolio_id)

    if request.method == "POST":
        portfolio_item.delete()
        messages.success(request, "Portfolio berhasil dihapus!")

    return redirect("main:show_portfolio")


def show_projects(request):
    title_query = request.GET.get("title", "").strip()
    selected_category = request.GET.get("category", "").strip()
    sort_mode = request.GET.get("sort", "position").strip()

    project_list = PortfolioItem.objects.order_by("display_order", "-created_at")

    if title_query:
        project_list = project_list.filter(title__icontains=title_query)

    if selected_category:
        project_list = project_list.filter(category=selected_category)

    if sort_mode == "latest":
        project_list = project_list.order_by("-created_at", "display_order")
    elif sort_mode == "oldest":
        project_list = project_list.order_by("created_at", "display_order")
    elif sort_mode == "title":
        project_list = project_list.order_by("title", "display_order")
    elif sort_mode == "starred":
        project_list = project_list.annotate(star_count=Count("starred_by")).order_by("-star_count", "display_order")

    project_list = list(project_list)

    if not project_list:
        project_list = [
            PortfolioItem(
                title="Bagaimana Cara Meningkatkan YouTube",
                description="Host: Bang Toon & DAVGAMER LIVE\nIklan Promosi: R-Bot\nNarasumber: YtDaN332",
                category="podcast",
                tech_stack="Podcast",
                project_url="#",
                display_order=0,
            ),
            PortfolioItem(
                title="Game Development",
                description="Project eksperimen pengembangan game dan video serta content creation.",
                category="game",
                tech_stack="Unity, C#",
                project_url="#",
                display_order=1,
            ),
        ]

    project_categories = list(
        PortfolioItem.objects.exclude(category="")
        .order_by("category")
        .values_list("category", flat=True)
        .distinct()
    )

    user_can_edit = request.user.is_authenticated and user_has_editor_access(request.user)
    user_can_delete = request.user.is_authenticated and user_has_editor_access(request.user)

    context = {
        "name": "Nadhif Aydin Adinandra",
        "project_list": project_list,
        "title_query": title_query,
        "selected_category": selected_category,
        "sort_mode": sort_mode,
        "project_categories": project_categories,
        "project_form": PortfolioItemForm(),
        "user_can_edit": user_can_edit,
        "user_can_delete": user_can_delete,
    }

    return render(request, "project.html", context)


def get_projects_json(request):
    title_query = request.GET.get("title", "").strip()
    selected_category = request.GET.get("category", "").strip()
    sort_mode = request.GET.get("sort", "position").strip()

    projects = PortfolioItem.objects.prefetch_related("starred_by", "comments__user").annotate(
        comment_count=Count("comments", distinct=True),
    )

    if title_query:
        projects = projects.filter(title__icontains=title_query)

    if selected_category:
        projects = projects.filter(category=selected_category)

    if sort_mode == "latest":
        projects = projects.order_by("-created_at", "display_order")
    elif sort_mode == "oldest":
        projects = projects.order_by("created_at", "display_order")
    elif sort_mode == "title":
        projects = projects.order_by("title", "display_order")
    elif sort_mode == "starred":
        projects = projects.annotate(star_count=Count("starred_by")).order_by("-star_count", "display_order")
    else:
        projects = projects.order_by("display_order", "-created_at")

    data = []
    for project in projects:
        starred_users = list(project.starred_by.all())
        is_starred = request.user in starred_users if request.user.is_authenticated else False
        data.append({
            "id": str(project.id),
            "title": project.title,
            "description": project.description,
            "category": project.category,
            "tech_stack": project.tech_stack,
            "project_url": project.project_url,
            "project_image_url": project.project_image_url,
            "star_count": len(starred_users),
            "comment_count": project.comment_count,
            "is_starred": is_starred,
            "starred_by_names": ", ".join(user.username for user in starred_users),
        })

    return JsonResponse(data, safe=False)


def _discussion_payload(item, user):
    return {
        "id": item.id,
        "username": item.user.username,
        "body": item.body,
        "reply_to": {
            "username": item.reply_to.user.username,
            "body": item.reply_to.body,
        } if item.reply_to_id else None,
        "created_at": timezone.localtime(item.created_at).strftime("%d %b %Y, %H:%M"),
        "can_edit": user.is_authenticated and item.user_id == user.pk,
        "url": reverse("main:chat_message_action", args=[item.id])
        if isinstance(item, ChatMessage)
        else reverse("main:project_comment_action", args=[item.id]),
    }


def _send_reply_notification(request, reply, subject, destination):
    parent = reply.reply_to
    if not parent or parent.user_id == reply.user_id or not parent.user.email:
        return False

    try:
        sent = send_mail(
            subject=subject,
            message=(
                f"Hi {parent.user.username},\n\n"
                f"{reply.user.username} replied to your {subject.lower()}:\n\n"
                f"{reply.body}\n\n"
                f"Open the conversation: {request.build_absolute_uri(destination)}\n"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[parent.user.email],
            fail_silently=False,
        )
        return sent == 1
    except Exception:
        logger.exception("Could not send reply notification email")
        return False


@login_required
def community_chat(request):
    return render(request, "community_chat.html", {
        "name": "Nadhif Aydin Adinandra",
    })


@require_http_methods(["GET", "POST"])
def chat_messages(request):
    if request.method == "GET":
        messages_list = ChatMessage.objects.select_related("user").order_by("-created_at")[:100]
        return JsonResponse(
            [_discussion_payload(item, request.user) for item in reversed(list(messages_list))],
            safe=False,
        )

    if not request.user.is_authenticated:
        return JsonResponse({"message": "Login untuk mengirim chat."}, status=403)

    body = strip_tags(request.POST.get("body", "")).strip()
    if not body:
        return JsonResponse({"message": "Pesan tidak boleh kosong."}, status=400)
    if len(body) > 2000:
        return JsonResponse({"message": "Pesan maksimal 2000 karakter."}, status=400)

    reply_to = None
    reply_to_id = request.POST.get("reply_to", "").strip()
    if reply_to_id:
        reply_to = get_object_or_404(ChatMessage, pk=reply_to_id)

    message = ChatMessage.objects.create(user=request.user, body=body, reply_to=reply_to)
    payload = _discussion_payload(message, request.user)
    payload["email_sent"] = _send_reply_notification(
        request,
        message,
        "Community chat reply",
        reverse("main:community_chat"),
    ) if reply_to else False
    return JsonResponse(payload, status=201)


@require_POST
def chat_message_action(request, message_id):
    if not request.user.is_authenticated:
        return JsonResponse({"message": "Login diperlukan."}, status=403)
    message = get_object_or_404(ChatMessage.objects.select_related("user"), pk=message_id)
    if message.user_id != request.user.pk:
        return JsonResponse({"message": "Kamu hanya dapat mengubah chat milikmu sendiri."}, status=403)

    action = request.POST.get("action")
    if action == "delete":
        message.delete()
        return JsonResponse({"status": "success", "message": "Pesan chat dihapus."})
    if action == "edit":
        body = strip_tags(request.POST.get("body", "")).strip()
        if not body:
            return JsonResponse({"message": "Pesan tidak boleh kosong."}, status=400)
        if len(body) > 2000:
            return JsonResponse({"message": "Pesan maksimal 2000 karakter."}, status=400)
        message.body = body
        message.save(update_fields=["body", "updated_at"])
        return JsonResponse(_discussion_payload(message, request.user))
    return JsonResponse({"message": "Aksi tidak valid."}, status=400)


@require_http_methods(["GET", "POST"])
def project_comments(request, project_id):
    project = get_object_or_404(PortfolioItem, pk=project_id)
    if request.method == "GET":
        comments = project.comments.select_related("user").order_by("created_at")
        return JsonResponse([_discussion_payload(item, request.user) for item in comments], safe=False)

    if not request.user.is_authenticated:
        return JsonResponse({"message": "Login untuk menulis komentar."}, status=403)
    body = strip_tags(request.POST.get("body", "")).strip()
    if not body:
        return JsonResponse({"message": "Komentar tidak boleh kosong."}, status=400)
    if len(body) > 2000:
        return JsonResponse({"message": "Komentar maksimal 2000 karakter."}, status=400)

    reply_to = None
    reply_to_id = request.POST.get("reply_to", "").strip()
    if reply_to_id:
        reply_to = get_object_or_404(ProjectComment, pk=reply_to_id)
        if reply_to.project_id != project.pk:
            return JsonResponse({"message": "Balasan harus berada di project yang sama."}, status=400)

    comment = ProjectComment.objects.create(project=project, user=request.user, body=body, reply_to=reply_to)
    payload = _discussion_payload(comment, request.user)
    payload["email_sent"] = _send_reply_notification(
        request,
        comment,
        "Project comment reply",
        reverse("main:show_projects"),
    ) if reply_to else False
    return JsonResponse(payload, status=201)


@require_POST
def project_comment_action(request, comment_id):
    if not request.user.is_authenticated:
        return JsonResponse({"message": "Login diperlukan."}, status=403)
    comment = get_object_or_404(ProjectComment.objects.select_related("user"), pk=comment_id)
    if comment.user_id != request.user.pk:
        return JsonResponse({"message": "Kamu hanya dapat mengubah komentarmu sendiri."}, status=403)

    action = request.POST.get("action")
    if action == "delete":
        project_id = str(comment.project_id)
        comment.delete()
        return JsonResponse({"status": "success", "message": "Komentar dihapus.", "project_id": project_id})
    if action == "edit":
        body = strip_tags(request.POST.get("body", "")).strip()
        if not body:
            return JsonResponse({"message": "Komentar tidak boleh kosong."}, status=400)
        if len(body) > 2000:
            return JsonResponse({"message": "Komentar maksimal 2000 karakter."}, status=400)
        comment.body = body
        comment.save(update_fields=["body", "updated_at"])
        return JsonResponse(_discussion_payload(comment, request.user))
    return JsonResponse({"message": "Aksi tidak valid."}, status=400)


def get_projects_xml(request):
    return get_portfolio_xml(request)


@login_required
@permission_required("main.add_portfolioitem", raise_exception=True)
def create_project(request):
    form = PortfolioItemForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        project = form.save()
        messages.success(request, "Project baru berhasil ditambahkan!")

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "status": "success",
                "message": "Project baru berhasil ditambahkan!",
                "project": {
                    "id": str(project.id),
                    "title": project.title,
                    "description": project.description,
                    "category": project.category,
                    "tech_stack": project.tech_stack,
                    "project_url": project.project_url,
                    "project_image_url": project.project_image_url,
                    "star_count": project.starred_by.count(),
                },
            }, status=201)

        return redirect("main:show_projects")

    if request.method == "POST" and not form.is_valid():
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"status": "error", "errors": form.errors.get_json_data()}, status=400)

    context = {
        "name": "Nadhif Aydin Adinandra",
        "form": form,
        "form_action_url": "main:create_project",
        "submit_button_text": "Tambah Project",
    }

    return render(request, "projects_form.html", context)


@login_required
@editor_required
def update_project(request, project_id):
    project_item = get_object_or_404(PortfolioItem, pk=project_id)
    form = PortfolioItemForm(request.POST or None, instance=project_item)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project berhasil diperbarui!")
        return redirect("main:show_projects")

    context = {
        "name": "Nadhif Aydin Adinandra",
        "form": form,
        "form_action_url": "main:update_project",
        "submit_button_text": "Simpan Perubahan",
        "update_object": project_item,
    }

    return render(request, "projects_form.html", context)


def show_portfolio_deserialized(request):
    title_query = request.GET.get("title", "").strip()
    portfolio_items = PortfolioItem.objects.all().order_by("created_at")

    if title_query:
        portfolio_items = portfolio_items.filter(title__icontains=title_query)

    context = {
        "name": "Nadhif Aydin Adinandra",
        "portfolio_items": list(portfolio_items),
    }

    return render(request, "portfolio_deserialized.html", context)


def show_projects_deserialized(request):
    project_list = list(PortfolioItem.objects.all().order_by("created_at"))

    if request.GET.get("title"):
        project_list = list(
            PortfolioItem.objects.filter(title__icontains=request.GET.get("title", "").strip())
            .order_by("created_at")
        )

    json_response = get_projects_json(request)
    serialized_data = json_response.content.decode("utf-8")
    deserialized_objects = list(serializers.deserialize("json", serialized_data))
    project_list = [item.object for item in deserialized_objects] or project_list

    context = {
        "name": "Nadhif Aydin Adinandra",
        "project_list": project_list,
    }

    return render(request, "project_deserialized.html", context)


@login_required
@editor_required
def delete_project(request, project_id):
    portfolio_item = get_object_or_404(PortfolioItem, pk=project_id)

    if request.method == "POST":
        portfolio_item.delete()
        messages.success(request, "Project berhasil dihapus!")

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "status": "success",
                "message": "Project berhasil dihapus.",
            })

    return redirect("main:show_projects")


def register(request):
    form = RegistrationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.email = form.cleaned_data["email"]
        user.save()
        profile, _ = UserProfile.objects.get_or_create(
            user=user,
            defaults={"full_name": form.cleaned_data["full_name"]},
        )
        profile.full_name = form.cleaned_data["full_name"]
        profile.save(update_fields=["full_name"])
        messages.success(request, "Akun berhasil dibuat. Silakan login.")
        return redirect("main:login")

    context = {
        "name": "Nadhif Aydin Adinandra",
        "form": form,
        "google_login_enabled": settings.GOOGLE_LOGIN_ENABLED,
    }
    return render(request, "register.html", context)


@login_required
def account_profile(request):
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "full_name": request.user.get_full_name() or request.user.username,
        },
    )

    if request.method == "POST":
        account_form = AccountDetailsForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        connections_formset = UserConnectionFormSet(request.POST, instance=profile, prefix="connections")
        if account_form.is_valid() and profile_form.is_valid() and connections_formset.is_valid():
            account_form.save()
            profile_form.save()
            connections_formset.save()
            messages.success(request, "Profile berhasil diperbarui.")
            return redirect("main:account_profile")
    else:
        account_form = AccountDetailsForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)
        connections_formset = UserConnectionFormSet(instance=profile, prefix="connections")

    profile_image_url = None
    if profile.profile_image and profile.profile_image.storage.exists(profile.profile_image.name):
        profile_image_url = profile.profile_image.url

    return render(request, "account_profile.html", {
        "name": "Nadhif Aydin Adinandra",
        "account_form": account_form,
        "profile_form": profile_form,
        "connections_formset": connections_formset,
        "profile": profile,
        "profile_image_url": profile_image_url,
    })


def public_member_profile(request, username):
    member = get_object_or_404(User, username=username)
    profile, _ = UserProfile.objects.get_or_create(
        user=member,
        defaults={"full_name": member.get_full_name() or member.username},
    )
    return render(request, "public_member_profile.html", {
        "name": "Nadhif Aydin Adinandra",
        "member": member,
        "profile": profile,
        "profile_image_url": profile.profile_image.url
        if profile.profile_image and profile.profile_image.storage.exists(profile.profile_image.name)
        else None,
        "connections": profile.connections.all(),
    })


def login_user(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        response = redirect("main:show_main")
        response.set_cookie(
            "last_login",
            timezone.localtime().strftime("%Y-%m-%d %H:%M:%S"),
            max_age=60 * 60 * 24 * 7,
            httponly=False,
        )
        return response

    context = {
        "name": "Nadhif Aydin Adinandra",
        "form": form,
        "google_login_enabled": settings.GOOGLE_LOGIN_ENABLED,
    }
    return render(request, "login.html", context)


def logout_user(request):
    logout(request)
    response = redirect("main:show_main")
    response.delete_cookie("last_login")
    return response


@login_required
def toggle_star(request, project_id):
    project = get_object_or_404(PortfolioItem, pk=project_id)

    if request.user in project.starred_by.all():
        project.starred_by.remove(request.user)
        message = "Star project dibatalkan."
        is_starred = False
    else:
        project.starred_by.add(request.user)
        message = "Project berhasil diberi star."
        is_starred = True

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "status": "success",
            "message": message,
            "star_count": project.starred_by.count(),
            "is_starred": is_starred,
        })

    return redirect("main:show_projects")


@login_required
@editor_required
@require_POST
def update_project_order(request):
    project_ids = request.POST.getlist("project_ids[]") or request.POST.getlist("project_ids")

    if not project_ids:
        return JsonResponse({"status": "error", "message": "No project ids provided."}, status=400)

    for order_index, project_id in enumerate(project_ids):
        PortfolioItem.objects.filter(pk=project_id).update(display_order=order_index)

    return JsonResponse({"status": "success", "updated": len(project_ids)})


@require_POST
def create_project_ajax(request):
    if not request.user.is_authenticated or not request.user.has_perm("main.add_portfolioitem"):
        return JsonResponse(
            {"status": "error", "message": "Kamu tidak memiliki izin untuk menambahkan project."},
            status=403,
        )

    form = ProjectForm(request.POST)
    if form.is_valid():
        project = form.save()
        return JsonResponse(
            {
                "status": "success",
                "message": "Project berhasil ditambahkan.",
                "project": {
                    "id": str(project.id),
                    "title": project.title,
                },
            },
            status=201,
        )

    return JsonResponse(
        {"status": "error", "message": "Periksa kembali data project.", "errors": form.errors.get_json_data()},
        status=400,
    )