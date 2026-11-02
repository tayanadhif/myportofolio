from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsPortfolioOwnerOrEditorOrReadOnly(BasePermission):
    message = "Only the portfolio owner can create or delete projects."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return (
            request.method in ("PUT", "PATCH")
            and user.has_perm("main.change_portfolioitem")
        )
