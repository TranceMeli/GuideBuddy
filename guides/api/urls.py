from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .. import views as page_views
from . import views

router = DefaultRouter()
router.register("guides", views.GuideViewSet, basename="guide")
router.register("categories", views.CategoryViewSet, basename="category")
router.register("reports", views.ReportViewSet, basename="report")
router.register("images", views.GuideImageViewSet, basename="image")

urlpatterns = [
    path("auth/register/", views.RegisterView.as_view(), name="api-register"),
    path("auth/verify/", views.VerifyEmailView.as_view(), name="api-verify"),
    path("auth/resend/", views.ResendVerificationView.as_view(), name="api-resend"),
    path("auth/login/", views.LoginView.as_view(), name="api-login"),
    path("auth/refresh/", views.RefreshView.as_view(), name="api-refresh"),
    path("auth/logout/", views.LogoutView.as_view(), name="api-logout"),
    path("auth/me/", views.MeView.as_view(), name="api-me"),
    path("markdown/render/", views.MarkdownRenderView.as_view(), name="api-markdown-render"),
    path("auth/password-reset/", views.PasswordResetRequestView.as_view(), name="api-reset"),
    path(
        "auth/password-reset/confirm/",
        views.PasswordResetConfirmView.as_view(),
        name="api-reset-confirm",
    ),
    path("auth/account/", views.AccountView.as_view(), name="api-account"),
    # The PDF is a plain Django view (not JSON), but lives under /api/
    path("guides/<slug:slug>/pdf/", page_views.guide_pdf, name="api-guide-pdf"),
    path("", include(router.urls)),
]
