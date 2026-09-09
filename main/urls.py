from django.urls import include, path

from main.views import show_experience, show_main, show_portfolio


app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("experience/", show_experience, name="show_experience"),
    path("portfolio/", show_portfolio, name="show_portfolio"),
]