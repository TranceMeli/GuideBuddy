from types import SimpleNamespace

from django.core.management.base import BaseCommand, CommandError

from guides.api.serializers import GuideSerializer
from guides.models import Category, Guide

EXAMPLE = "install-python-on-windows"

NL = chr(10)

# The sample guides follow the rules for good guides (docs/guide-types.md): the goal first, a
# warning before the first step, materials with quantities, one action per step with the expected
# result, an outcome that says how to check it, troubleshooting as "If you see ... then ...".
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
            {"kind": "section", "text": "What you need"},
            {"kind": "checklist", "text": "A Windows 10 or 11 PC" + NL + "Administrator rights on this PC" + NL + "About 200 MB of free disk space"},
            {"kind": "section", "text": "Download the installer"},
            {"kind": "step", "text": "Open the download page"},
            {"kind": "text", "text": "Open [the Python downloads page](https://www.python.org/downloads/) and click **Download Python 3.13**."},
            {"kind": "warning", "text": "Download Python only from **python.org**. Installers from other sites can contain malware."},
            {"kind": "result", "text": "A file named `python-3.13.0-amd64.exe` appears in your Downloads folder."},
            {"kind": "section", "text": "Install Python"},
            {"kind": "step", "text": "Start the installer"},
            {"kind": "text", "text": "Double-click the downloaded file. Tick **Add python.exe to PATH**, then click **Install Now**."},
            {"kind": "result", "text": "The installer copies the files and shows a progress bar."},
            {"kind": "error", "text": "Forgot the tick? The command prompt later says *“python” is not recognised*. Run the installer again and tick the box."},
            {"kind": "section", "text": "Check that it works"},
            {"kind": "step", "text": "Check the version"},
            {"kind": "terminal", "text": "$ python --version" + NL + "Python 3.13.0"},
            {"kind": "result", "text": "The terminal shows `Python 3.13.0` or a newer version."},
            {"kind": "section", "text": "Outcome"},
            {"kind": "result", "text": "`python --version` shows a version number. You can now run Python programs on this PC."},
            {"kind": "section", "text": "If something goes wrong"},
            {"kind": "table", "data": {"rows": [["If you see …", "Then …"], ["“python” is not recognised", "Run the installer again and tick **Add python.exe to PATH**."], ["A Microsoft Store window opens", "Turn off the Python app aliases in Windows Settings and open the terminal again."]]}},
            {"kind": "section", "text": "Related guides"},
            {"kind": "link", "text": "The official Python tutorial", "data": {"url": "https://docs.python.org/3/tutorial/"}},
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
            {"kind": "text", "text": "You will bake a crusty loaf in a Dutch oven. Use this guide if you already have a starter and have never baked sourdough. Plan for **one evening and one morning**; the active work is about 90 minutes."},
            {"kind": "warning", "text": "The Dutch oven is **250 °C hot**. Use oven gloves and never touch the pot or the lid with bare hands."},
            {"kind": "section", "text": "What you need"},
            {"kind": "checklist", "text": "500 g bread flour" + NL + "350 g water, lukewarm" + NL + "100 g active sourdough starter" + NL + "10 g salt" + NL + "A Dutch oven with a lid, a large bowl and a kitchen scale"},
            {"kind": "collapsible", "text": "I do not have a starter", "data": {"body": "Mix 50 g flour and 50 g water in a jar every day for seven days, discarding half before each feeding. It is ready when it doubles in size within 6 hours."}},
            {"kind": "section", "text": "Make the dough"},
            {"kind": "step", "text": "Mix flour, water and starter"},
            {"kind": "text", "text": "In the large bowl, stir 500 g flour, 350 g water and 100 g starter until no dry flour is left. Cover the bowl and rest for 30 minutes."},
            {"kind": "result", "text": "The dough is shaggy and sticky, with no dry patches."},
            {"kind": "step", "text": "Add the salt"},
            {"kind": "text", "text": "Sprinkle 10 g salt on top and fold the dough over itself about ten times."},
            {"kind": "tip", "text": "Wet your hand before touching the dough. It will not stick."},
            {"kind": "result", "text": "The salt is mixed in and the dough feels tighter."},
            {"kind": "step", "text": "Fold the dough three times"},
            {"kind": "text", "text": "Repeat the folding every 30 minutes, three times in total."},
            {"kind": "result", "text": "The dough is smoother and holds its shape a little."},
            {"kind": "diagram", "text": "From mixing to bread", "data": {"nodes": ["Mix", "Rest", "Fold", "Rise overnight", "Shape", "Bake"]}},
            {"kind": "section", "text": "Rise and bake"},
            {"kind": "step", "text": "Let the dough rise"},
            {"kind": "text", "text": "Cover the bowl and leave it for 8 to 12 hours at room temperature."},
            {"kind": "result", "text": "The dough has grown by about half, jiggles when you shake the bowl and has bubbles on the surface."},
            {"kind": "step", "text": "Bake the loaf"},
            {"kind": "text", "text": "Heat the Dutch oven with the lid on to 250 °C for 30 minutes. Score the loaf, put it in and bake as shown:"},
            {"kind": "table", "data": {"rows": [["Phase", "Temperature", "Time"], ["With lid", "250 °C", "20 minutes"], ["Without lid", "230 °C", "20 to 25 minutes"]]}},
            {"kind": "result", "text": "The crust is golden brown when you take off the lid."},
            {"kind": "section", "text": "Outcome"},
            {"kind": "result", "text": "The loaf is deep brown and sounds hollow when you tap the underside. Let it cool for one hour before you cut it."},
            {"kind": "section", "text": "If something goes wrong"},
            {"kind": "table", "data": {"rows": [["If you see …", "Then …"], ["A pale, flat loaf", "Let the dough rise less and preheat the pot for the full 30 minutes."], ["A gummy crumb", "Wait one hour before you cut the loaf."]]}},
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
            {"kind": "text", "text": "White flakes inside the kettle are limescale. They are harmless, but they slow down heating and change the taste of tea. This guide removes them in about 30 minutes."},
            {"kind": "warning", "text": "Unplug the kettle before you clean it, and never mix vinegar with bleach or other cleaners."},
            {"kind": "section", "text": "What you need"},
            {"kind": "checklist", "text": "White vinegar (about 300 ml) or 2 tablespoons of citric acid powder" + NL + "Water" + NL + "A soft sponge"},
            {"kind": "section", "text": "Descale"},
            {"kind": "step", "text": "Fill the kettle"},
            {"kind": "text", "text": "Fill it halfway with water, then add the same amount of white vinegar. With citric acid, add two tablespoons of powder instead."},
            {"kind": "result", "text": "The kettle is half full of a clear mix that smells of vinegar."},
            {"kind": "step", "text": "Heat the mix"},
            {"kind": "text", "text": "Bring the mix to the boil, switch the kettle off and leave it for **20 minutes**."},
            {"kind": "result", "text": "The limescale has loosened and floats in the water."},
            {"kind": "step", "text": "Rinse the kettle"},
            {"kind": "text", "text": "Pour the liquid away and wipe the inside with a sponge. Fill the kettle with fresh water, boil it and pour it away. Do this twice."},
            {"kind": "tip", "text": "In hard water areas, descale about once a month."},
            {"kind": "result", "text": "The water is clear and has no white flakes."},
            {"kind": "compare", "text": "Which cleaner for the kettle?", "data": {"wrong": "Scouring powder or a steel brush", "right": "Vinegar or citric acid with a soft sponge", "language": ""}},
            {"kind": "section", "text": "Outcome"},
            {"kind": "result", "text": "The inside is clean and the water no longer smells of vinegar."},
            {"kind": "section", "text": "If something goes wrong"},
            {"kind": "table", "data": {"rows": [["If you see …", "Then …"], ["Limescale is still there", "Repeat once with fresh vinegar and leave it for an hour."], ["The water smells of vinegar", "Boil fresh water once more and pour it away."]]}},
            {"kind": "collapsible", "text": "Can I use lemon juice?", "data": {"body": "Yes. Use the juice of two lemons with water, but strain it afterwards; the pulp can stay in the spout."}},
        ],
    },
]


class Command(BaseCommand):
    help = "Create the sample guides (skips guides that already exist)."

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
