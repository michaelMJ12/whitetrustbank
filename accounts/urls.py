
from django.urls import path

from . import views


app_name = "accounts"


urlpatterns = [
    # Authentication
    path(
        "login/",
        views.login_view,
        name="login",
    ),

    path(
        "signup/",
        views.signup_view,
        name="signup",
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),

    # Password reset request
    path(
        "password-reset/",
        views.password_reset_request_view,
        name="password_reset",
    ),

    # Password reset confirmation
    path(
        "reset/<uidb64>/<token>/",
        views.password_reset_confirm_view,
        name="password_reset_confirm",
    ),
]
