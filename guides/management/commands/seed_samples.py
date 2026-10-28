from types import SimpleNamespace

from django.core.management.base import BaseCommand, CommandError

from guides.api.serializers import GuideSerializer
from guides.models import Category, Guide

EXAMPLE = "install-python-on-windows"

SAMPLES = [
    {
        "guide_type": "page",
        "title": "Install Python on Windows",
        "subtitle": "From the download to your first program in 15 minutes",
        "summary": "Install Python on a Windows PC, check that it works and run a first program.",
        "difficulty": "beginner",
        "duration_minutes": 15,
        "category": "computers-technology",
        "elements": [
            {"kind": "text", "text": "This guide takes you from the download to a running program. It is meant for **beginners without prior knowledge**."},
            {"kind": "checklist", "text": "A Windows 10 or 11 PC" + chr(10) + "Administrator rights on this PC" + chr(10) + "About 200 MB of free disk space"},
            {"kind": "section", "text": "Download the installer"},
            {"kind": "step", "text": "Open the download page"},
            {"kind": "text", "text": "Open [the Python downloads page](https://www.python.org/downloads/) and click **Download Python 3.13**."},
            {"kind": "important", "text": "Download Python only from **python.org**. Installers from other sites can contain malware."},
            {"kind": "result", "text": "A file named `python-3.13.0-amd64.exe` appears in your Downloads folder."},
            {"kind": "section", "text": "Install Python"},
            {"kind": "step", "text": "Start the installer"},
            {"kind": "text", "text": "Double-click the downloaded file. Tick **Add python.exe to PATH**, then click **Install Now**."},
            {"kind": "error", "text": "Forgot the tick? The command prompt later says *“python” is not recognised*. Run the installer again and tick the box."},
            {"kind": "section", "text": "Check that it works"},
            {"kind": "step", "text": "Check the version"},
            {"kind": "terminal", "text": "$ python --version" + chr(10) + "Python 3.13.0"},
            {"kind": "result", "text": "The terminal shows `Python 3.13.0` or a newer version."},
        ],
    },
    {
        "guide_type": "page",
        "title": "Bake Sourdough Bread at Home",
        "subtitle": "A first loaf with a starter, flour, water and salt",
        "summary": "Bake a crusty sourdough loaf with a Dutch oven, from mixing the dough to the first slice.",
        "difficulty": "intermediate",
        "duration_minutes": 90,
        "category": "cooking-baking",
        "elements": [
            {"kind": "text", "text": "Sourdough needs time more than skill. Plan for **one evening and one morning**; the active work is about 90 minutes."},
            {"kind": "checklist", "text": "500 g bread flour" + chr(10) + "350 g water, lukewarm" + chr(10) + "100 g active sourdough starter" + chr(10) + "10 g salt" + chr(10) + "A Dutch oven with a lid"},
            {"kind": "section", "text": "Make the dough"},
            {"kind": "step", "text": "Mix"},
            {"kind": "text", "text": "Stir flour, water and starter in a large bowl until no dry flour is left. Cover and rest for 30 minutes."},
            {"kind": "step", "text": "Add the salt and fold"},
            {"kind": "text", "text": "Sprinkle the salt on top and fold the dough over itself about ten times. Repeat the folding three times, every 30 minutes."},
            {"kind": "tip", "text": "Wet your hand before touching the dough. It will not stick."},
            {"kind": "diagram", "text": "From mixing to bread", "data": {"nodes": ["Mix", "Rest", "Fold", "Rise overnight", "Shape", "Bake"]}},
            {"kind": "section", "text": "Rise and bake"},
            {"kind": "step", "text": "Let the dough rise"},
            {"kind": "text", "text": "Cover the bowl and leave it for 8 to 12 hours at room temperature, until it has grown by about half."},
            {"kind": "result", "text": "The dough is puffy, jiggles when you shake the bowl and has bubbles on the surface."},
            {"kind": "step", "text": "Bake"},
            {"kind": "text", "text": "Heat the Dutch oven with the lid on to 250 °C for 30 minutes. Score the loaf, put it in and bake as shown:"},
            {"kind": "table", "data": {"rows": [["Phase", "Temperature", "Time"], ["With lid", "250 °C", "20 minutes"], ["Without lid", "230 °C", "20 to 25 minutes"]]}},
            {"kind": "important", "text": "The pot is **extremely hot**. Use oven gloves and never touch the lid with bare hands."},
            {"kind": "error", "text": "A pale, flat loaf usually means the dough rose too long or the pot was not hot enough."},
            {"kind": "collapsible", "text": "I do not have a starter", "data": {"body": "Mix 50 g flour and 50 g water in a jar every day for seven days, discarding half before each feeding. It is ready when it doubles in size within 6 hours."}},
        ],
    },
    {
        "guide_type": "page",
        "title": "Descale a Kettle with Vinegar",
        "subtitle": "Remove limescale in 30 minutes with a household remedy",
        "summary": "Remove limescale from an electric kettle with vinegar or citric acid and rinse it safely.",
        "difficulty": "beginner",
        "duration_minutes": 30,
        "category": "household",
        "elements": [
            {"kind": "text", "text": "White flakes inside the kettle are limescale. They are harmless, but they slow down heating and change the taste of tea."},
            {"kind": "checklist", "text": "White vinegar or citric acid powder" + chr(10) + "Water" + chr(10) + "A soft sponge"},
            {"kind": "important", "text": "Unplug the kettle before you clean it, and never mix vinegar with bleach or other cleaners."},
            {"kind": "section", "text": "Descale"},
            {"kind": "step", "text": "Fill the kettle"},
            {"kind": "text", "text": "Fill it halfway with water, then add the same amount of white vinegar. With citric acid, use two tablespoons of powder instead."},
            {"kind": "step", "text": "Heat and wait"},
            {"kind": "text", "text": "Bring the mix to the boil, switch the kettle off and leave it for **20 minutes**."},
            {"kind": "step", "text": "Rinse"},
            {"kind": "text", "text": "Pour the liquid away and wipe the inside with a sponge. Fill the kettle with fresh water, boil it and pour it away. Do this twice."},
            {"kind": "result", "text": "The inside is clean and the water no longer smells of vinegar."},
            {"kind": "tip", "text": "In hard water areas, descale about once a month."},
            {"kind": "compare", "text": "Which cleaner for the kettle?", "data": {"wrong": "Scouring powder or a steel brush", "right": "Vinegar or citric acid with a soft sponge", "language": ""}},
            {"kind": "section", "text": "If it does not work"},
            {"kind": "error", "text": "Limescale is still there after the first round? Repeat once with fresh vinegar and leave it for an hour."},
            {"kind": "collapsible", "text": "Can I use lemon juice?", "data": {"body": "Yes. Use the juice of two lemons with water, but strain it afterwards; the pulp can stay in the spout."}},
        ],
    },
]


class Command(BaseCommand):
    help = "Create the sample guide (skips guides that already exist)."

    def handle(self, *args, **options):
        default_category = Category.objects.filter(slug="computers-technology").first()
        request = SimpleNamespace(user=None)
        for sample in SAMPLES:
            data = dict(sample)
            if Guide.objects.filter(title=data["title"]).exists():
                self.stdout.write(f"exists: {data['title']}")
                continue
            category = Category.objects.filter(slug=data.pop("category", "")).first() or default_category
            data["category_id"] = category.id if category else None
            data["change_comment"] = "Sample guide"
            serializer = GuideSerializer(data=data, context={"request": request})
            if not serializer.is_valid():
                raise CommandError(f"{data['title']}: {serializer.errors}")
            guide = serializer.save()
            self.stdout.write(self.style.SUCCESS(f"created: /guides/{guide.slug} ({guide.guide_type})"))
