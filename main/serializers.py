import re

from django.utils.html import strip_tags
from rest_framework import serializers

from main.models import PortfolioItem


class PortfolioItemSerializer(serializers.ModelSerializer):
    star_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    is_starred = serializers.SerializerMethodField()

    class Meta:
        model = PortfolioItem
        fields = [
            "id", "title", "description", "category", "tech_stack",
            "project_url", "project_image_url", "display_order",
            "star_count", "comment_count", "is_starred",
        ]
        read_only_fields = ["id", "display_order", "star_count", "comment_count", "is_starred"]

    def _sanitize_text(self, value, preserve_newlines=False):
        # Remove script contents before strip_tags(), which removes markup but
        # can leave the text inside a script element behind.
        cleaned = re.sub(r"(?is)<script\b[^>]*>.*?</script\s*>", "", value)
        cleaned = strip_tags(cleaned)
        if preserve_newlines:
            cleaned = "\n".join(
                re.sub(r"[ \t]+", " ", line).strip()
                for line in cleaned.splitlines()
            )
            return re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        return re.sub(r"\s{2,}", " ", cleaned).strip()

    def validate_title(self, value):
        value = self._sanitize_text(value)
        if not value:
            raise serializers.ValidationError("Title cannot be empty.")
        return value

    def validate_description(self, value):
        return self._sanitize_text(value, preserve_newlines=True)

    def validate_tech_stack(self, value):
        return self._sanitize_text(value)

    def validate_category(self, value):
        return self._sanitize_text(value)

    def get_star_count(self, obj):
        count = getattr(obj, "api_star_count", None)
        return count if count is not None else obj.starred_by.count()

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

