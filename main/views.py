from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from main.forms import PortfolioItemForm
from main.models import Experience, PortfolioItem


def show_main(request):
    context = {
        "name": "Nadhif Aydin Adinandra",
        "npm": "2506537745",
        "study_program": "S1 Ilmu Komputer",
        "bio": (
            "Computer Science student at Universitas Indonesia interested in programming, mathematics, and game development. Outside of academics, I also create gaming content on YouTube, sharing gameplay, longplays, and other gaming projects. Feel free to check out my channel and see what I do beyond Fasilkom. I also enjoy exploring new technologies and staying up-to-date with the latest trends in the tech world. My passion for learning drives me to continuously improve my skills and contribute to exciting projects."
        ),
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

    portfolio_items_json = serializers.serialize("json", portfolio_items)
    return HttpResponse(portfolio_items_json, content_type="application/json")


def create_portfolio_item(request):
    form = PortfolioItemForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Portfolio baru berhasil ditambahkan!")
        return redirect("main:show_portfolio")

    context = {
        "name": "Nadhif Aydin Adinandra",
        "form": form,
    }

    return render(request, "portfolio_form.html", context)


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

    context = {
        "name": "Nadhif Aydin Adinandra",
        "project_list": list(project_list),
        "title_query": title_query,
    }

    return render(request, "project.html", context)


def get_projects_json(request):
    return get_portfolio_json(request)


def create_project(request):
    form = PortfolioItemForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project baru berhasil ditambahkan!")
        return redirect("main:show_projects")

    context = {
        "name": "Nadhif Aydin Adinandra",
        "form": form,
    }

    return render(request, "projects_form.html", context)


def delete_project(request, project_id):
    portfolio_item = get_object_or_404(PortfolioItem, pk=project_id)

    if request.method == "POST":
        portfolio_item.delete()
        messages.success(request, "Project berhasil dihapus!")

    return redirect("main:show_projects")