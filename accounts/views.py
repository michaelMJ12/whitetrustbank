
import logging

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .forms import LoginForm, SignupForm
from .services import EmailService


logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURATION
# ============================================================

PASSWORD_RESET_CONFIRM_URL_NAME = "accounts:password_reset_confirm"
PASSWORD_RESET_REQUEST_URL_NAME = "accounts:password_reset"

PASSWORD_RESET_REQUESTED_MESSAGE = (
    "If an account exists for that email address, "
    "we have sent instructions to reset your password."
)


# ============================================================
# ROLE-BASED REDIRECTION
# ============================================================

def _redirect_for_role(user):
    """Redirect authenticated users to the appropriate dashboard."""

    if user.role == "admin":
        return redirect("banking:admin_dashboard")

    return redirect("banking:dashboard")


# ============================================================
# LOGIN VIEW
# ============================================================

def login_view(request):

    login_form = LoginForm()
    signup_form = SignupForm()
    password_reset_form = PasswordResetRequestForm()

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

                # Establish authenticated session first.
                login(request, user)

                logger.info(
                    "User authentication successful; "
                    "role-based redirect follows."
                )

                # Email must never interrupt successful authentication.
                send_login_email = getattr(
                    settings,
                    "SEND_LOGIN_EMAILS",
                    False,
                )

                if send_login_email:

                    email_sent = False

                    try:
                        email_sent = EmailService.send_login_email(user)

                    except Exception:
                        logger.exception(
                            "Login notification email failed for user %s",
                            user.pk,
                        )

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
                            "could not be sent. You can continue using "
                            "your account.",
                        )

                else:
                    messages.success(
                        request,
                        "Login successful.",
                    )

                # Always redirect after successful authentication.
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
            "password_reset_form": password_reset_form,
            "active": active,
        },
    )


# ============================================================
# SIGNUP VIEW
# ============================================================

def signup_view(request):

    login_form = LoginForm()
    signup_form = SignupForm()
    password_reset_form = PasswordResetRequestForm()

    if request.method == "POST":

        signup_form = SignupForm(request.POST)

        if signup_form.is_valid():

            # Create user.
            user = signup_form.save()

            # Send welcome email.
            try:

                email_sent = EmailService.send_signup_email(user)

                if email_sent:

                    messages.success(
                        request,
                        "Your account was created successfully. "
                        "A welcome email has been sent to your email address.",
                    )

                    logger.info(
                        "Signup email sent successfully to %s",
                        user.email,
                    )

                else:

                    messages.warning(
                        request,
                        "Your account was created successfully, "
                        "but we could not send the welcome email.",
                    )

                    logger.warning(
                        "Signup email could not be sent to %s",
                        user.email,
                    )

            except Exception:

                logger.exception(
                    "Unexpected signup email error for %s",
                    user.email,
                )

                messages.warning(
                    request,
                    "Your account was created successfully, "
                    "but we could not send the welcome email.",
                )

            # Log in newly registered user.
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
            "password_reset_form": password_reset_form,
            "active": "signup",
        },
    )


# ============================================================
# LOGOUT VIEW
# ============================================================

def logout_view(request):

    logout(request)

    return redirect("landing")


# ============================================================
# PASSWORD RESET REQUEST FORM
# ============================================================

class PasswordResetRequestForm(forms.Form):

    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "Enter your email address",
                "class": (
                    "w-full rounded-xl border border-slate-200 "
                    "px-4 py-3 outline-none focus:border-teal"
                ),
            }
        ),
    )


# ============================================================
# PASSWORD RESET HELPERS
# ============================================================

def _get_reset_candidates(email):
    """
    Return active accounts matching the supplied email address
    and having a usable password.
    """

    User = get_user_model()

    users = User.objects.filter(
        email__iexact=email,
        is_active=True,
    )

    return [
        user
        for user in users
        if user.has_usable_password()
    ]


def _get_user_from_uid(uidb64):
    """
    Decode the user ID from the password-reset URL.
    Return None if the ID is invalid.
    """

    User = get_user_model()

    try:

        user_pk = force_str(
            urlsafe_base64_decode(uidb64)
        )

        return User.objects.get(
            pk=user_pk,
            is_active=True,
        )

    except (
        TypeError,
        ValueError,
        OverflowError,
        User.DoesNotExist,
    ):

        return None


# ============================================================
# SEND PASSWORD RESET EMAIL
# ============================================================

def _send_password_reset_email(request, user):
    """
    Generate and send a password-reset link.

    Django's default token generator validates the token and
    invalidates it after the user's password changes.
    """

    uid = urlsafe_base64_encode(
        force_bytes(user.pk)
    )

    token = default_token_generator.make_token(user)

    reset_path = reverse(
        PASSWORD_RESET_CONFIRM_URL_NAME,
        kwargs={
            "uidb64": uid,
            "token": token,
        },
    )

    reset_url = request.build_absolute_uri(reset_path)

    timeout_hours = max(
        1,
        settings.PASSWORD_RESET_TIMEOUT // 3600,
    )

    subject = "Reset your White Trust Bank password"

    body = (
        "Hello,\n\n"
        "We received a request to reset the password "
        "for your White Trust Bank account.\n\n"
        "Use the link below to choose a new password:\n\n"
        f"{reset_url}\n\n"
        f"This link expires in {timeout_hours} hour(s). "
        "After successfully changing your password, "
        "the link will no longer be valid.\n\n"
        "If you did not request this password reset, "
        "you can safely ignore this email. "
        "Your password will not change.\n\n"
        "Regards,\n"
        "White Trust Bank Security Team"
    )

    try:

        send_mail(
            subject,
            body,
            getattr(
                settings,
                "DEFAULT_FROM_EMAIL",
                None,
            ),
            [user.email],
            fail_silently=False,
        )

        logger.info(
            "Password reset email sent successfully to %s",
            user.email,
        )

        return True

    except Exception:

        # Never log reset tokens or complete reset URLs.
        logger.exception(
            "Unexpected error sending password reset email."
        )

        return False


# ============================================================
# PASSWORD RESET REQUEST VIEW
# ============================================================

def password_reset_request_view(request):
    """
    Step 1:
    Accept the user's email and send a password-reset link.
    """

    login_form = LoginForm()
    signup_form = SignupForm()
    form = PasswordResetRequestForm()

    if request.method == "POST":

        form = PasswordResetRequestForm(request.POST)

        if form.is_valid():

            email = form.cleaned_data["email"]

            users = _get_reset_candidates(email)

            for user in users:

                _send_password_reset_email(
                    request,
                    user,
                )

            # Always show the same response.
            # This prevents account-email enumeration.
            messages.success(
                request,
                PASSWORD_RESET_REQUESTED_MESSAGE,
            )

            # Use a fresh form after submission.
            form = PasswordResetRequestForm()

    return render(
        request,
        "accounts/login.html",
        {
            "login_form": login_form,
            "signup_form": signup_form,
            "password_reset_form": form,
            "active": "forgot",
        },
    )


# ============================================================
# PASSWORD RESET CONFIRMATION VIEW
# ============================================================

def password_reset_confirm_view(request, uidb64, token):
    """
    Step 2:
    Validate the emailed token and allow the user
    to choose a new password.
    """

    user = _get_user_from_uid(uidb64)

    link_is_valid = (
        user is not None
        and default_token_generator.check_token(
            user,
            token,
        )
    )

    login_form = LoginForm()
    signup_form = SignupForm()
    password_reset_form = PasswordResetRequestForm()

    # Invalid or expired reset link.
    if not link_is_valid:

        return render(
            request,
            "accounts/login.html",
            {
                "login_form": login_form,
                "signup_form": signup_form,
                "password_reset_form": password_reset_form,
                "active": "reset",
                "valid_link": False,
            },
            status=400,
        )

    form = SetPasswordForm(user)

    if request.method == "POST":

        # Validate the token again before accepting the password.
        if not default_token_generator.check_token(
            user,
            token,
        ):

            return render(
                request,
                "accounts/login.html",
                {
                    "login_form": login_form,
                    "signup_form": signup_form,
                    "password_reset_form": password_reset_form,
                    "active": "reset",
                    "valid_link": False,
                },
                status=400,
            )

        form = SetPasswordForm(
            user,
            request.POST,
        )

        if form.is_valid():

            form.save()

            logger.info(
                "Password successfully reset for user ID %s",
                user.pk,
            )

            messages.success(
                request,
                "Your password has been reset successfully. "
                "You can now log in using your new password.",
            )

            return redirect("accounts:login")

    return render(
        request,
        "accounts/login.html",
        {
            "login_form": login_form,
            "signup_form": signup_form,
            "password_reset_form": password_reset_form,
            "reset_form": form,
            "active": "reset",
            "valid_link": True,
        },
    )
