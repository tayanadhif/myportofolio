import mimetypes

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import migrations


def preserve_existing_data(apps, schema_editor):
    Contact = apps.get_model("main", "Contact")
    User = apps.get_model("auth", "User")
    UserProfile = apps.get_model("main", "UserProfile")
    StoredMedia = apps.get_model("main", "StoredMedia")
    database = schema_editor.connection.alias

    legacy_owner = User.objects.using(database).filter(is_superuser=True).order_by("id").first()
    if legacy_owner is None and User.objects.using(database).count() == 1:
        legacy_owner = User.objects.using(database).first()
    if legacy_owner is not None:
        Contact.objects.using(database).filter(owner__isnull=True).update(owner_id=legacy_owner.pk)

    old_storage = FileSystemStorage(location=settings.MEDIA_ROOT)
    for profile in UserProfile.objects.using(database).exclude(profile_image="").iterator():
        name = profile.profile_image
        if StoredMedia.objects.using(database).filter(name=name).exists() or not old_storage.exists(name):
            continue
        with old_storage.open(name, "rb") as image_file:
            content = image_file.read()
        StoredMedia.objects.using(database).create(
            name=name,
            content=content,
            content_type=mimetypes.guess_type(name)[0] or "",
            size=len(content),
        )


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0014_storedmedia_alter_userprofile_profile_image"),
    ]

    operations = [
        migrations.RunPython(preserve_existing_data, migrations.RunPython.noop),
    ]
