# error handling middleware
from django.core.exceptions import PermissionDenied
from django.shortcuts import render


class PermissionDeniedErrorHandler:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, PermissionDenied):
            return render(
                request=request,
                template_name="unauthorized_access.html",
                status=403
            )
        return None