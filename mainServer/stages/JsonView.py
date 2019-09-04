import json
from functools import wraps
from django.http import HttpResponseServerError
from django.http import HttpResponse

from django.http import HttpResponseBadRequest
from django.views import View


class JsonViewException(Exception):
    def __init__(self, errorClass):
        if not isinstance(errorClass, HttpResponse):
            raise AssertionError("errorClass should inherit django.http.HttpResponse")

        self.errorClass = errorClass


def django_exceptions(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        try:
            return view_func(*args, **kwargs)
        except JsonViewException as e:
            return e.errorClass
        except Exception as e:
            return HttpResponseServerError(str(e))

    return wrapper


class JsonView(View):
    """
    This class adds abstract level for getting data from request. It get data from params in GET and from JSON in any
    other http method

    It should be use by inheritance and implements appropriate method for http methods we wants to serve
    Method names are in scheme {http_method_name}_method()
    f.e. http.GET -> get_method()   ;   http.PUT -> put_method()   ;   http.DELETE -> delete_method()
    if you want get some data from request you can use self.get_data(...) method or self.get_data_or_error(...)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._data = None
        self._request = None
        for method_name in self.http_method_names:
            setattr(self, method_name, self._method_template(method_name))

    @django_exceptions
    def _method_template(self, method_name):
        return lambda request, **kwargs: self._run_method(method_name, request, **kwargs)

    def _run_method(self, fun_name: str, request, **kwargs):
        self._request = request
        if fun_name == 'get':
            self._data = None
        else:
            self._data = json.loads(request.read().decode('utf-8').replace("'", "\""))

        method_to_run = getattr(self, f"{fun_name}_method", lambda: self.http_method_not_allowed(request, **kwargs))
        return method_to_run()

    def get_data(self, key, default=None, allow_empty_value=False):
        if self._data:
            try:
                return self._data[key] if allow_empty_value else self._data[key] if self._data[key] != '' else default
            except KeyError:
                return default
        else:
            if allow_empty_value:
                return self._request.GET.get(key, default)
            else:
                ret = self._request.GET.get(key, default)
                if ret == '':
                    ret = default

                return ret

    def get_data_or_error(self, key, error=HttpResponseBadRequest()):
        if self._data:
            if key in self._data:
                return self._data[key]
            else:
                raise JsonViewException(error)
        else:
            data = self._request.GET.get(key, None)
            if not data:
                raise JsonViewException(error)
            else:
                return data
