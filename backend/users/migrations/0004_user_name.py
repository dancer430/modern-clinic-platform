from django.db import migrations, models


def backfill_user_name(apps, schema_editor):
    User = apps.get_model("users", "User")
    for user in User._default_manager.all():
        full_name = f"{user.first_name} {user.last_name}".strip()
        user.name = full_name or user.username
        user.save(update_fields=["name"])


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0003_platformsetting"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="name",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.RunPython(backfill_user_name, migrations.RunPython.noop),
    ]
