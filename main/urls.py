from django.contrib.auth import views
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
    login_user,
    logout_user,
    register,
    show_experience,
    show_main,
    show_portfolio,
    show_portfolio_deserialized,
    show_projects,
    show_projects_deserialized,
    toggle_star,
    update_portfolio_item,
    update_project,
    update_project_order,
)


app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("experience/", show_experience, name="show_experience"),
    path("portfolio/", show_portfolio, name="show_portfolio"),
    path("projects/", show_projects, name="show_projects"),
    path("portfolio/add/", create_portfolio_item, name="create_portfolio_item"),
    path("projects/add/", create_project, name="create_project"),
    path("portfolio/<uuid:portfolio_id>/update/", update_portfolio_item, name="update_portfolio_item"),
    path("projects/<uuid:project_id>/update/", update_project, name="update_project"),
    path("portfolio/<uuid:portfolio_id>/delete/", delete_portfolio_item, name="delete_portfolio_item"),
    path("projects/<uuid:project_id>/delete/", delete_project, name="delete_project"),
    path("portfolio/deserialized/", show_portfolio_deserialized, name="show_portfolio_deserialized"),
    path("projects/deserialized/", show_projects_deserialized, name="show_projects_deserialized"),
    path("api/portfolio/", get_portfolio_json, name="get_portfolio_json"),
    path("api/portfolio/xml/", get_portfolio_xml, name="get_portfolio_xml"),
    path("api/projects/", get_projects_json, name="get_projects_json"),
    path("api/projects/xml/", get_projects_xml, name="get_projects_xml"),
    path("register/", register, name="register"),
    path("login/", login_user, name="login"),
    path("logout/", logout_user, name="logout"),
    path("projects/<uuid:project_id>/star/", toggle_star, name="toggle_star"),
    path("projects/reorder/", update_project_order, name="update_project_order"),
]