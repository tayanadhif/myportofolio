from functools import wraps

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from main.forms import PortfolioItemForm
from main.models import Experience, PortfolioItem


EDITOR_REQUIRED_PERMISSIONS = (
    "main.add_portfolioitem",
    "main.change_portfolioitem",
    "main.delete_portfolioitem",
)


def user_has_editor_access(user):
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if user.groups.filter(name="Editor").exists():
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
    title_query = request.GET.get("title", "").strip()
    portfolio_items = PortfolioItem.objects.order_by("created_at")

    if title_query:
        portfolio_items = portfolio_items.filter(title__icontains=title_query)

    portfolio_items = list(portfolio_items)

    if not portfolio_items:
        portfolio_items = [
            PortfolioItem(
                title="Portfolio Website",
                description="A personal portfolio website built with Django to present my profile, experience, and projects.",
                category="featured",
                link="https://nadhif-aydin-myportofolio.pws.cs.ui.ac.id/",
            ),
            PortfolioItem(
                title="Game Development",
                description="Creating gameplay videos, longplays, and gaming projects while developing editing and digital content production skills.",
                category="game",
            ),
        ]

    context = {
        "name": "Nadhif Aydin Adinandra",
        "portfolio_items": portfolio_items,
        "title_query": title_query,
    }

    return render(request, "portfolio.html", context)


def get_portfolio_json(request):
    title_query = request.GET.get("title", "").strip()
    portfolio_items = PortfolioItem.objects.all()

    if title_query:
        portfolio_items = portfolio_items.filter(title__icontains=title_query)

    portfolio_items_json = serializers.serialize("json", portfolio_items, use_natural_foreign_keys=True)

    return HttpResponse(portfolio_items_json, content_type="application/json")


def get_portfolio_xml(request):
    title_query = request.GET.get("title", "").strip()
    portfolio_items = PortfolioItem.objects.all()

    if title_query:
        portfolio_items = portfolio_items.filter(title__icontains=title_query)

    portfolio_items_xml = serializers.serialize("xml", portfolio_items)
    return HttpResponse(portfolio_items_xml, content_type="application/xml")


@login_required
@editor_required
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
    project_list = PortfolioItem.objects.order_by("created_at")

    if title_query:
        project_list = project_list.filter(title__icontains=title_query)

    project_list = list(project_list)

    if not project_list:
        project_list = [
            PortfolioItem(
                title="Bagaimana Cara Meningkatkan YouTube",
                description="Host: Bang Toon & DAVGAMER LIVE\nIklan Promosi: R-Bot\nNarasumber: YtDaN332",
                category="podcast",
                tech_stack="Podcast",
                project_url="#",
            ),
            PortfolioItem(
                title="Game Development",
                description="Project eksperimen pengembangan game dan video serta content creation.",
                category="game",
                tech_stack="Unity, C#",
                project_url="#",
            ),
        ]

    context = {
        "name": "Nadhif Aydin Adinandra",
        "project_list": project_list,
        "title_query": title_query,
    }

    return render(request, "project.html", context)


def get_projects_json(request):
    return get_portfolio_json(request)


def get_projects_xml(request):
    return get_portfolio_xml(request)


@login_required
@editor_required
def create_project(request):
    form = PortfolioItemForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project baru berhasil ditambahkan!")
        return redirect("main:show_projects")

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
    portfolio_items = list(PortfolioItem.objects.all().order_by("created_at"))

    if request.GET.get("title"):
        portfolio_items = list(
            PortfolioItem.objects.filter(title__icontains=request.GET.get("title", "").strip())
            .order_by("created_at")
        )

    json_response = get_portfolio_json(request)
    serialized_data = json_response.content.decode("utf-8")
    deserialized_objects = list(serializers.deserialize("json", serialized_data))
    portfolio_items = [item.object for item in deserialized_objects] or portfolio_items

    context = {
        "name": "Nadhif Aydin Adinandra",
        "portfolio_items": portfolio_items,
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

    return redirect("main:show_projects")


def register(request):
    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Akun berhasil dibuat. Silakan login.")
        return redirect("main:login")

    context = {
        "name": "Nadhif Aydin Adinandra",
        "form": form,
    }
    return render(request, "register.html", context)


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
    else:
        project.starred_by.add(request.user)

    return redirect("main:show_projects")