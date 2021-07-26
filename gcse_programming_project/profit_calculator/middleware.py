from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse_lazy


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.login_url = reverse_lazy(settings.LOGIN_URL)
        self.open_urls = [self.login_url] + [
            reverse_lazy(url) for url in getattr(settings, "OPEN_URLS", [])
        ]

    def __call__(self, request):
        if (
            not request.user.is_authenticated
            and request.path not in self.open_urls
            and not request.path.startswith("/admin/")
        ):
            return redirect(self.login_url + "?next=" + request.path)

        return self.get_response(request)
