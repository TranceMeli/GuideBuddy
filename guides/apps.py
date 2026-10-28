from django.apps import AppConfig


class GuidesConfig(AppConfig):
    name = "guides"

    def ready(self):
        from . import checks  # noqa: F401  (registers the production check)
