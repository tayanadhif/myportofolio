from django.urls import path

from main import api_views

app_name = "api"

urlpatterns = [
    path("projects/", api_views.portfolio_item_list, name="project-list"),
    path("projects/<uuid:item_id>/", api_views.portfolio_item_detail, name="project-detail"),
    path("projects/<uuid:item_id>/star/", api_views.portfolio_item_star, name="project-star"),
]
