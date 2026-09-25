from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0005_portfolioitem_starred_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="portfolioitem",
            name="display_order",
            field=models.PositiveIntegerField(db_index=True, default=0),
        ),
    ]
