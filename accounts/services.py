
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


class EmailService:
    """
    Centralized email service for White Trust Bank.

    Email delivery failures are logged and returned as False
    instead of crashing the main login or signup workflow.
    """

    @staticmethod
    def send_email(
        subject,
        recipient,
        text_content,
        html_content=None,
    ):
        """Send an email and safely handle SMTP failures."""

        if not recipient:
            logger.error("Email not sent: recipient address is missing.")
            return False

        email_user = getattr(settings, "EMAIL_HOST_USER", "")
        email_password = getattr(settings, "EMAIL_HOST_PASSWORD", "")

        if not email_user or not email_password:
            logger.error(
                "Email not sent: Gmail SMTP credentials are not configured."
            )
            return False

        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient],
            )

            if html_content:
                email.attach_alternative(html_content, "text/html")

            sent_count = email.send(fail_silently=False)

            if sent_count == 1:
                logger.info(
                    "Email sent successfully. Subject: %s",
                    subject,
                )
                return True

            logger.error(
                "Email backend did not send the message. Subject: %s",
                subject,
            )
            return False

        except Exception:
            # Logs the traceback in Render without logging credentials.
            logger.exception(
                "Email delivery failed. Subject: %s",
                subject,
            )
            return False

    @staticmethod
    def send_signup_email(user):
        """Send a welcome email after signup."""

        first_name = getattr(user, "first_name", "") or "Customer"
        recipient = getattr(user, "email", "")

        subject = "Welcome to White Trust Bank"

        text_content = f"""Hello {first_name},

Welcome to White Trust Bank.

Your account has been successfully created using:

Email: {recipient}

You can now log in and access your White Trust Bank account.

If you did not create this account, please contact our support team.

Regards,
White Trust Bank
"""

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Welcome to White Trust Bank</title>
</head>
<body style="margin:0;padding:30px;background-color:#f4f7f5;font-family:Arial,Helvetica,sans-serif;">
    <div style="max-width:600px;margin:0 auto;background:#ffffff;padding:35px;border-radius:12px;">
        <h1 style="color:#0F5C4E;">Welcome to White Trust Bank</h1>
        <p>Hello <strong>{first_name}</strong>,</p>
        <p>Your White Trust Bank account has been successfully created.</p>
        <p>Your registered email address is: <strong>{recipient}</strong></p>
        <p>You can now log in and access your account.</p>
        <p style="margin-top:30px;">If you did not create this account, please contact our support team.</p>
        <hr style="margin:30px 0;border:none;border-top:1px solid #eeeeee;">
        <p style="color:#777777;">Regards,<br><strong>White Trust Bank</strong></p>
    </div>
</body>
</html>"""

        return EmailService.send_email(
            subject=subject,
            recipient=recipient,
            text_content=text_content,
            html_content=html_content,
        )

    @staticmethod
    def send_login_email(user):
        """Send a security notification after successful login."""

        first_name = getattr(user, "first_name", "") or "Customer"
        recipient = getattr(user, "email", "")

        subject = "New login to your White Trust Bank account"

        text_content = f"""Hello {first_name},

Your White Trust Bank account was just used to log in.

Account: {recipient}

If this was you, no action is required.

If you do not recognize this login, please change your password
and contact White Trust Bank support immediately.

Regards,
White Trust Bank
"""

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>White Trust Bank Login Notification</title>
</head>
<body style="margin:0;padding:30px;background-color:#f4f7f5;font-family:Arial,Helvetica,sans-serif;">
    <div style="max-width:600px;margin:0 auto;background:#ffffff;padding:35px;border-radius:12px;">
        <h2 style="color:#0F5C4E;">New Login Detected</h2>
        <p>Hello <strong>{first_name}</strong>,</p>
        <p>Your White Trust Bank account was just used to log in.</p>
        <div style="background:#f4f7f5;padding:15px;border-radius:8px;margin:20px 0;">
            <strong>Account</strong><br>{recipient}
        </div>
        <p>If this was you, no action is required.</p>
        <p>If you do not recognize this login, please change your password
        and contact White Trust Bank support immediately.</p>
        <hr style="margin:30px 0;border:none;border-top:1px solid #eeeeee;">
        <p style="color:#777777;">Regards,<br><strong>White Trust Bank</strong></p>
    </div>
</body>
</html>"""

        return EmailService.send_email(
            subject=subject,
            recipient=recipient,
            text_content=text_content,
            html_content=html_content,
        )
