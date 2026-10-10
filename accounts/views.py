from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from .forms import LoginForm, SignupForm
from .services import EmailService


def _redirect_for_role(user):
    return redirect(
        "banking:admin_dashboard"
        if user.role == "admin"
        else "banking:dashboard"
    )


import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render

from .forms import LoginForm, SignupForm
from .services import EmailService

logger = logging.getLogger(__name__)


def login_view(request):
    login_form = LoginForm()
    signup_form = SignupForm()

    active = (
        "signup"
        if request.GET.get("mode") == "signup"
        else "login"
    )

    if request.method == "POST":
        login_form = LoginForm(request.POST)

        if login_form.is_valid():
            user = authenticate(
                request,
                username=login_form.cleaned_data["email"],
                password=login_form.cleaned_data["password"],
            )

            if user is not None:
                # Establish the authenticated session first.
                login(request, user)

                logger.info(
                    "User authentication successful; role-based redirect follows."
                )

                # Email delivery must not prevent a successful login.
                try:
                    email_sent = EmailService.send_login_email(user)

                    if email_sent:
                        messages.success(
                            request,
                            "Login successful. A security notification "
                            "has been sent to your email.",
                        )
                    else:
                        messages.warning(
                            request,
                            "Login successful, but the security notification "
                            "could not be sent. You can continue using your account.",
                        )

                except Exception:
                    logger.exception(
                        "Unexpected error while sending login notification."
                    )

                    messages.warning(
                        request,
                        "Login successful, but the security notification "
                        "could not be sent.",
                    )

                return _redirect_for_role(user)

            login_form.add_error(
                None,
                "That email or password doesn't match our records.",
            )

        active = "login"

    return render(
        request,
        "accounts/login.html",
        {
            "login_form": login_form,
            "signup_form": signup_form,
            "active": active,
        },
    )


def signup_view(request):

    login_form = LoginForm()
    signup_form = SignupForm()

    if request.method == "POST":

        signup_form = SignupForm(request.POST)

        if signup_form.is_valid():

            # ----------------------------------------
            # CREATE USER
            # ----------------------------------------
            user = signup_form.save()

            # ----------------------------------------
            # SEND WELCOME EMAIL
            # ----------------------------------------
            try:
                result = EmailService.send_signup_email(user)
                print("sing_up successful...")
                if result:
                    messages.success(
                        request,
                        "Your account was created successfully. "
                        "A welcome email has been sent to your email address.",
                    )

                    print(
                        f"[EMAIL SUCCESS] Signup email sent successfully "
                        f"to {user.email}"
                    )

                else:
                    messages.warning(
                        request,
                        "Your account was created successfully, "
                        "but we could not send the welcome email.",
                    )

                    print(
                        f"[EMAIL FAILED] Signup email was not sent "
                        f"to {user.email}"
                    )

            except Exception as e:

                messages.warning(
                    request,
                    "Your account was created successfully, "
                    "but we could not send the welcome email.",
                )

                print(
                    f"[EMAIL ERROR] Signup email failed for "
                    f"{user.email}: {type(e).__name__}: {e}"
                )

            # ----------------------------------------
            # LOGIN USER
            # ----------------------------------------
            login(
                request,
                user,
                backend="accounts.backends.EmailBackend",
            )

            return redirect("banking:dashboard")

    return render(
        request,
        "accounts/login.html",
        {
            "login_form": login_form,
            "signup_form": signup_form,
            "active": "signup",
        },
    )


def logout_view(request):
    logout(request)
    return redirect("landing")
