from django.core.management.base import BaseCommand

from guides.models import Category, Guide, Step


class Command(BaseCommand):
    help = "Create a sample category and a sample guide."

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(name="Computers & Technology")
        guide, created = Guide.objects.get_or_create(
            title="Set up a Python environment",
            defaults={
                "category": category,
                "summary": "How to set up a virtual environment for Python.",
            },
        )
        if created:
            Step.objects.bulk_create(
                [
                    Step(
                        guide=guide,
                        order=1,
                        title="Create a folder",
                        body="Create a project folder and change into it:\n\n"
                        "```bash\nmkdir my-project\ncd my-project\n```",
                    ),
                    Step(
                        guide=guide,
                        order=2,
                        title="Create the virtual environment",
                        body="```bash\npython -m venv .venv\n```",
                    ),
                    Step(
                        guide=guide,
                        order=3,
                        title="Activate the environment",
                        body="Linux/macOS: `source .venv/bin/activate`\n\n"
                        "Windows: `.venv\\Scripts\\activate`",
                    ),
                ]
            )
        self.stdout.write(self.style.SUCCESS("Demo data created."))
