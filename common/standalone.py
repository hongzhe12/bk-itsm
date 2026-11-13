from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.http import JsonResponse


def login_required(get_response):
    def middleware(request):
        if request.user.is_authenticated or request.path.startswith(
            (settings.STATIC_URL, settings.MEDIA_URL, settings.LOGIN_URL, "/admin/", "/openapi/")
        ):
            return get_response(request)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "result": False,
                    "code": "LOGIN_REQUIRED",
                    "message": "请先登录",
                    "login_url": settings.LOGIN_URL,
                },
                status=401,
            )
        return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)

    return middleware
