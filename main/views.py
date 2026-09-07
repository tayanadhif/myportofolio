from django.shortcuts import render
from main.models import Experience


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
    context = {
        "name": "Nadhif Aydin Adinandra",
        "experience_list": Experience.objects.all(),
    }

    return render(request, "experience.html", context)