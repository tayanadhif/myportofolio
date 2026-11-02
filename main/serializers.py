from django.utils.html import strip_tags
from rest_framework import serializers

from main.models import PortfolioItem


class PortfolioItemSerializer(serializers.ModelSerializer):
    star_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()
    starred_by_names = serializers.SerializerMethodField()

    class Meta:
        model = PortfolioItem
        fields = [
            "id", "title", "description", "category", "tech_stack",
            "project_url", "project_image_url", "display_order",
            "star_count", "comment_count", "is_starred", "starred_by_names",
        ]
        read_only_fields = ["id", "display_order"]

    def validate_title(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Title cannot be empty.")
        return value

    def validate_description(self, value):
        return strip_tags(value)

    def validate_tech_stack(self, value):
        return strip_tags(value)

    def validate_category(self, value):
        return strip_tags(value)

    def get_star_count(self, obj):
        return len(obj.starred_by.all())

    def get_comment_count(self, obj):
        count = getattr(obj, "api_comment_count", None)
        return count if count is not None else obj.comments.count()

    def get_is_starred(self, obj):
        request = self.context.get("request")
        return bool(
            request
            and request.user.is_authenticated
            and obj.starred_by.filter(pk=request.user.pk).exists()
        )

    def get_starred_by_names(self, obj):
        return ", ".join(user.username for user in obj.starred_by.all())
