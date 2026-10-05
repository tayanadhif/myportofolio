from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.urls import reverse
from django.utils.deconstruct import deconstructible


@deconstructible
class DatabaseMediaStorage(Storage):
    """Store uploaded media in the configured database, not the app container."""

    def _record_model(self):
        from main.models import StoredMedia

        return StoredMedia

    def _open(self, name, mode="rb"):
        record = self._record_model().objects.get(name=name)
        return ContentFile(bytes(record.content), name=name)

    def _save(self, name, content):
        content.open("rb")
        data = b"".join(content.chunks())
        self._record_model().objects.update_or_create(
            name=name,
            defaults={
                "content": data,
                "content_type": getattr(content, "content_type", "") or "",
                "size": len(data),
            },
        )
        return name

    def delete(self, name):
        self._record_model().objects.filter(name=name).delete()

    def exists(self, name):
        return self._record_model().objects.filter(name=name).exists()

    def size(self, name):
        return self._record_model().objects.values_list("size", flat=True).get(name=name)

    def url(self, name):
        return reverse("main:serve_media", kwargs={"name": name})
