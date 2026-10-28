from django.db import migrations

MODERATOR_GROUP = "Moderatoren"


def forwards(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    User = apps.get_model("auth", "User")
    Profile = apps.get_model("guides", "Profile")

    Group.objects.get_or_create(name=MODERATOR_GROUP)

    # Bestehende Konten stammen aus der Zeit vor der E-Mail-Bestätigung und gelten
    # als bestätigt (sonst würde "cleanup_unverified" sie später löschen).
    for user in User.objects.filter(profile__isnull=True):
        Profile.objects.create(user=user, email_verified_at=user.date_joined)


class Migration(migrations.Migration):
    dependencies = [
        ("guides", "0002_accounts_moderation"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
