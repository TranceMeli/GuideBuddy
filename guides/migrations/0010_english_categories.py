from django.db import migrations

# The default categories of 0007, renamed for the English interface. Only categories that
# still have their original name and slug are touched; renamed ones are left alone.
RENAMES = [
    ("Computer & Technik", "computer-technik", "Computers & Technology", "computers-technology"),
    ("Handy & Apps", "handy-apps", "Phones & Apps", "phones-apps"),
    ("Haushalt", "haushalt", "Household", "household"),
    ("Kochen & Backen", "kochen-backen", "Cooking & Baking", "cooking-baking"),
    ("Heimwerken", "heimwerken", "DIY & Home Improvement", "diy-home-improvement"),
    ("Garten", "garten", "Garden", "garden"),
    ("Auto & Fahrrad", "auto-fahrrad", "Cars & Bikes", "cars-bikes"),
    ("Gesundheit", "gesundheit", "Health", "health"),
    ("Geld & Behörden", "geld-behorden", "Money & Paperwork", "money-paperwork"),
    ("Freizeit & Hobby", "freizeit-hobby", "Leisure & Hobbies", "leisure-hobbies"),
    ("Sonstiges", "sonstiges", "Other", "other"),
]


def rename(apps, schema_editor, forward=True):
    Category = apps.get_model("guides", "Category")
    for old_name, old_slug, new_name, new_slug in RENAMES:
        source = (old_name, old_slug) if forward else (new_name, new_slug)
        target = (new_name, new_slug) if forward else (old_name, old_slug)
        if Category.objects.filter(name=target[0]).exists() or Category.objects.filter(slug=target[1]).exists():
            continue
        Category.objects.filter(name=source[0], slug=source[1]).update(name=target[0], slug=target[1])


class Migration(migrations.Migration):
    dependencies = [("guides", "0009_english_labels_and_language")]

    operations = [
        migrations.RunPython(rename, lambda apps, schema_editor: rename(apps, schema_editor, forward=False))
    ]
