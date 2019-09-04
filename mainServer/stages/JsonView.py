import json
import inspect
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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._data = None
        self._request = None

    @django_exceptions
    def get(self, request, **kwargs):
        this_fun_name = inspect.currentframe().f_code.co_name
        return self.run_method(this_fun_name, request, **kwargs)

    @django_exceptions
    def post(self, request, **kwargs):
        this_fun_name = inspect.currentframe().f_code.co_name
        return self.run_method(this_fun_name, request, **kwargs)

    @django_exceptions
    def delete(self, request, **kwargs):
        this_fun_name = inspect.currentframe().f_code.co_name
        return self.run_method(this_fun_name, request, **kwargs)

    @django_exceptions
    def put(self, request, **kwargs):
        this_fun_name = inspect.currentframe().f_code.co_name
        return self.run_method(this_fun_name, request, **kwargs)

    def run_method(self, fun_name: str, request, **kwargs):
        if fun_name == 'get':
            self._data = None
            self._request = request
        else:
            self._data = json.loads(request.read().decode('utf-8').replace("'", "\""))
            self._request = request

        method_to_run = getattr(self, f"{fun_name}_method", lambda: self.http_method_not_allowed(request, **kwargs))
        return method_to_run()

    def _get_data(self, key, default=None, allow_empty_value=False):
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

    def _get_data_or_error(self, key, error=HttpResponseBadRequest()):
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
