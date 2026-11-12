from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render


class SystemShutdownMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        state = cache.get("system_shutdown") or {}

        if state.get("active"):
            # Only the startup endpoint stays reachable so the
            # admin can bring the system back online.
            if request.path.startswith("/api/admin/system/startup/"):
                return self.get_response(request)

            if request.path.startswith("/api/"):
                return JsonResponse(
                    {
                        "ok": False,
                        "error": state.get(
                            "message",
                            "System is temporarily down for maintenance.",
                        ),
                    },
                    status=503,
                )

            return render(request, "maintenance.html", status=503)

        return self.get_response(request)