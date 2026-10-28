import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from .forms import GuideForm, StepFormSet
from .models import Category, Guide
from .pdf import PdfUnavailable, render_pdf
from .pdf_elements import render_elements_html
from .permissions import write_denial


def _search(queryset, query):
    query = (query or "").strip()
    if not query:
        return queryset
    return queryset.filter(
        Q(title__icontains=query)
        | Q(summary__icontains=query)
        | Q(steps__title__icontains=query)
        | Q(steps__body__icontains=query)
        | Q(elements__text__icontains=query)
    ).distinct()


def _list_response(request, guides, **context):
    query = request.GET.get("q", "")
    guides = _search(guides, query).select_related("category")
    context.update({"guides": guides, "q": query})
    # HTMX only asks for the list fragment (live search)
    if request.headers.get("HX-Request"):
        return render(request, "guides/_guide_list.html", context)
    context["categories"] = Category.objects.all()
    return render(request, "guides/home.html", context)


def home(request):
    return _list_response(request, Guide.objects.all())


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    return _list_response(request, category.guides.all(), category=category)


def guide_detail(request, slug):
    guide = get_object_or_404(Guide.objects.select_related("category"), slug=slug)
    steps = list(guide.steps.all())
    jsonld = {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": guide.title,
        "description": guide.summary,
        "step": [
            {"@type": "HowToStep", "position": i, "name": s.title, "text": s.body}
            for i, s in enumerate(steps, start=1)
        ],
    }
    # escape "</" so the content cannot end the <script> tag
    jsonld_str = json.dumps(jsonld, ensure_ascii=False).replace("</", "<\\/")
    return render(
        request,
        "guides/guide_detail.html",
        {"guide": guide, "steps": steps, "jsonld": jsonld_str},
    )


def guide_pdf(request, slug):
    guide = get_object_or_404(Guide.objects.select_related("category"), slug=slug)
    context = {
        "guide": guide,
        "steps": guide.steps.all(),
        "elements_html": render_elements_html(guide) if guide.guide_type == "page" else "",
        "frontend_url": settings.FRONTEND_URL.rstrip("/"),
    }
    try:
        pdf = render_pdf(
            html=render_to_string("guides/guide_pdf.html", context, request=request),
            simple_html=render_to_string("guides/guide_pdf_simple.html", context, request=request),
            base_url=request.build_absolute_uri("/"),
        )
    except PdfUnavailable:
        return HttpResponse(
            "PDF export is not set up on this server "
            "(neither WeasyPrint nor xhtml2pdf can be used).",
            status=503,
            content_type="text/plain; charset=utf-8",
        )
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{guide.slug}.pdf"'
    return response


@login_required
def guide_create(request):
    return _edit(request, Guide(created_by=request.user), is_new=True)


@login_required
def guide_edit(request, slug):
    guide = get_object_or_404(Guide, slug=slug)
    return _edit(request, guide, is_new=False)


def _edit(request, guide, is_new):
    # Same rules as in the API (new accounts, locked guides, bans)
    denial = write_denial(request.user, None if is_new else guide)
    if denial:
        messages.error(request, denial)
        return render(request, "guides/forbidden.html", {"message": denial}, status=403)
    if request.method == "POST":
        form = GuideForm(request.POST, instance=guide)
        formset = StepFormSet(request.POST, instance=guide)
        if form.is_valid() and formset.is_valid():
            saved = form.save(commit=False)
            comment = form.cleaned_data.get("change_comment")
            saved._change_reason = comment or ("Guide created" if is_new else "Guide edited")
            saved.save()
            formset.instance = saved
            formset.save()
            return redirect(saved)
    else:
        form = GuideForm(instance=guide)
        formset = StepFormSet(instance=guide)
    return render(
        request,
        "guides/guide_form.html",
        {"form": form, "formset": formset, "guide": guide, "is_new": is_new},
    )


def guide_history(request, slug):
    guide = get_object_or_404(Guide, slug=slug)
    guide_changes = guide.history.select_related("history_user")
    step_changes = (
        guide.steps.model.history.filter(guide_id=guide.pk)
        .select_related("history_user")
        .order_by("-history_date")
    )
    return render(
        request,
        "guides/guide_history.html",
        {"guide": guide, "guide_changes": guide_changes, "step_changes": step_changes},
    )


def register(request):
    """Registration only exists in the new frontend (with e-mail confirmation)."""
    return redirect(f"{settings.FRONTEND_URL.rstrip('/')}/registrieren")
