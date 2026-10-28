from django.urls import path

from . import views

app_name = "guides"

urlpatterns = [
    path("", views.home, name="home"),
    path("kategorie/<slug:slug>/", views.category_detail, name="category"),
    path("guides/neu/", views.guide_create, name="create"),
    path("guides/<slug:slug>/", views.guide_detail, name="detail"),
    path("guides/<slug:slug>/bearbeiten/", views.guide_edit, name="edit"),
    path("guides/<slug:slug>/verlauf/", views.guide_history, name="history"),
    path("guides/<slug:slug>/pdf/", views.guide_pdf, name="pdf"),
]
