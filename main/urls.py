from django.urls import include, path

from main.views import (
    create_portfolio_item,
    create_project,
    delete_portfolio_item,
    delete_project,
    get_portfolio_json,
    get_portfolio_xml,
    get_projects_json,
    get_projects_xml,
    show_experience,
    show_main,
    show_portfolio,
    show_projects,
)


app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("experience/", show_experience, name="show_experience"),
    path("portfolio/", show_portfolio, name="show_portfolio"),
    path("projects/", show_projects, name="show_projects"),
    path("portfolio/add/", create_portfolio_item, name="create_portfolio_item"),
    path("projects/add/", create_project, name="create_project"),
    path("portfolio/<uuid:portfolio_id>/delete/", delete_portfolio_item, name="delete_portfolio_item"),
    path("projects/<uuid:portfolio_id>/delete/", delete_project, name="delete_project"),
    path("api/portfolio/", get_portfolio_json, name="get_portfolio_json"),
    path("api/portfolio/xml/", get_portfolio_xml, name="get_portfolio_xml"),
    path("api/projects/", get_projects_json, name="get_projects_json"),
    path("api/projects/xml/", get_projects_xml, name="get_projects_xml"),
]