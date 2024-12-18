from django.core.exceptions import PermissionDenied

def check_perm(function):
    def wrap(request, *args, **kwargs):
        user = request.user
        func_name = function.__name__
        if user.has_perm(func_name):
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    wrap.__doc__ = function.__doc__
    wrap.__name__ = function.__name__
    return wrap