from django.db import migrations
from django.utils.text import slugify

DEFAULT_CATEGORIES = [
    "Computer & Technik",
    "Handy & Apps",
    "Haushalt",
    "Kochen & Backen",
    "Heimwerken",
    "Garten",
    "Auto & Fahrrad",
    "Gesundheit",
    "Geld & Behörden",
    "Freizeit & Hobby",
    "Sonstiges",
]


def add_defaults(apps, schema_editor):
    """Create the default categories, but only if there are none yet."""
    Category = apps.get_model("guides", "Category")
    if Category.objects.exists():
        return
    Category.objects.bulk_create(
        Category(name=name, slug=slugify(name)) for name in DEFAULT_CATEGORIES
    )


class Migration(migrations.Migration):
    dependencies = [("guides", "0006_guide_attachment_historicalguide_attachment")]

    operations = [migrations.RunPython(add_defaults, migrations.RunPython.noop)]
