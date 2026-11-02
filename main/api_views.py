from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view, authentication_classes, permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from main.models import PortfolioItem
from main.permissions import IsPortfolioOwnerOrEditorOrReadOnly
from main.serializers import PortfolioItemSerializer


def _project_queryset(request):
    projects = PortfolioItem.objects.prefetch_related("starred_by").annotate(
        api_comment_count=Count("comments", distinct=True),
        api_star_count=Count("starred_by", distinct=True),
    )
    title = request.query_params.get("title", "").strip()
    category = request.query_params.get("category", "").strip()
    sort_mode = request.query_params.get("sort", "position").strip()
    if title:
        projects = projects.filter(title__icontains=title)
    if category:
        projects = projects.filter(category=category)
    if sort_mode == "latest":
        return projects.order_by("-created_at", "display_order", "id")
    if sort_mode == "oldest":
        return projects.order_by("created_at", "display_order", "id")
    if sort_mode == "title":
        return projects.order_by("title", "display_order", "id")
    if sort_mode == "starred":
        return projects.order_by("-api_star_count", "display_order", "id")
    return projects.order_by("display_order", "-created_at", "id")


@api_view(["GET", "HEAD", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def portfolio_item_list(request):
    if request.method in ("GET", "HEAD"):
        serializer = PortfolioItemSerializer(
            _project_queryset(request), many=True, context={"request": request},
        )
        return Response(serializer.data)

    serializer = PortfolioItemSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsPortfolioOwnerOrEditorOrReadOnly])
def portfolio_item_detail(request, item_id):
    item = get_object_or_404(
        PortfolioItem.objects.prefetch_related("starred_by"), pk=item_id,
    )
    if request.method in ("GET", "HEAD"):
        return Response(PortfolioItemSerializer(item, context={"request": request}).data)
    if request.method == "DELETE":
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = PortfolioItemSerializer(
        item, data=request.data, partial=request.method == "PATCH",
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def portfolio_item_star(request, item_id):
    item = get_object_or_404(PortfolioItem, pk=item_id)
    stars = item.starred_by
    if stars.filter(pk=request.user.pk).exists():
        stars.remove(request.user)
    else:
        stars.add(request.user)
    item = PortfolioItem.objects.prefetch_related("starred_by").get(pk=item.pk)
    return Response(PortfolioItemSerializer(item, context={"request": request}).data)
