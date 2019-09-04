import json
from abc import ABC, abstractmethod
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


class JsonView(View, ABC):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._data = None
        self._request = None

    @abstractmethod
    def post_method(self):
        pass

    @abstractmethod
    def get_method(self):
        pass

    @django_exceptions
    def get(self, request, **kwargs):
        self._data = None
        self._request = request
        return self.get_method()

    @django_exceptions
    def post(self, request, **kwargs):
        self._data = json.loads(request.read().decode('utf-8').replace("'", "\""))
        self._request = request
        return self.post_method()

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
