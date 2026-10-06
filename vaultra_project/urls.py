from django.contrib import admin
from django.templatetags import static
from django.urls import path, include
from banking.views import landing_page

urlpatterns = [
    path("django-admin/", admin.site.urls),  # Django's built-in admin (separate from our Bank Control dashboard)
    path("", landing_page, name="landing"),
    path("accounts/", include("accounts.urls")),
    path("", include("banking.urls")),
]
