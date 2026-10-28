from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from guides import views as guide_views
from guides.sitemaps import CategorySitemap, GuideSitemap

sitemaps = {"guides": GuideSitemap, "categories": CategorySitemap}

urlpatterns = [
    path("admin/", admin.site.urls),
    # Only login/logout for the Django pages; password reset goes through the API
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("registrieren/", guide_views.register, name="register"),
    path("api/", include("guides.api.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("", include("guides.urls")),
]
