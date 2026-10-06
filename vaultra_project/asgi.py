import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vaultra_project.settings")
application = get_asgi_application()

# PRODUCTION NOTE: the live transaction monitor currently works by the
# browser polling GET /api/live-status/ once a second. That's simple and
# needs nothing beyond plain Django, but a real-time push (Django Channels
# + this ASGI app + a WebSocket consumer per account) would remove the
# polling delay and cut request volume. Swapping it in later doesn't
# require changing the LiveTransactionStatus model — only how updates
# reach the browser.
