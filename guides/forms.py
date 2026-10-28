from django import forms
from django.forms import inlineformset_factory

from .models import Guide, Step


class GuideForm(forms.ModelForm):
    change_comment = forms.CharField(
        label="Change comment",
        required=False,
        max_length=200,
        help_text="Briefly describe what you changed (shown in the history).",
    )

    class Meta:
        model = Guide
        fields = ["title", "category", "summary"]
        widgets = {"summary": forms.Textarea(attrs={"rows": 3})}


StepFormSet = inlineformset_factory(
    Guide,
    Step,
    fields=["order", "title", "body"],
    extra=1,
    can_delete=True,
    widgets={"body": forms.Textarea(attrs={"rows": 6})},
)
