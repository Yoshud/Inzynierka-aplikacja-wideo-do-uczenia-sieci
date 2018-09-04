import json
from django.http import HttpResponseBadRequest
from mainServer.models import *
import os
from os import walk
from django.http import Http404
from django.views.generic import View
from abc import ABC, abstractmethod

endPositionStatus = "Koniec"
userPositionStatus = "Dodane uzytkownik"
interpolatedPositonStatus = "Interpolacja"


def filterFilms(files):
    filmSufixes = [".mp4", ".avi", ".mpeg", ".mpg", ".h264"]
    return list(filter(lambda file: any([sufix in file for sufix in filmSufixes]), files))


def validateReturnForPath(folders):
    if folders == None:
        raise Http404


def foldersAndMovieFilesFromPath(path):
    _, foldernames, filenames = next(walk(path), (None, None, []))
    validateReturnForPath(foldernames)
    filenames = filterFilms(filenames)
    return foldernames, filenames


def pathUp(path):
    return os.path.dirname(path)


def currentPath():
    return os.getcwd()


def getMultipleMovieStatuses(statuses):
    return [StatusFilmu.objects.get_or_create(status=status)[0]
            for status in statuses]


def removeMultipleStatuses(movie, statuses):
    for status in getMultipleMovieStatuses(statuses):
        movie.status.remove(status)


def addToDictDefaultList(dict, dictElement, elementToAdd):
    try:
        dict[dictElement].append(elementToAdd)
    except KeyError:
        dictElement[dictElement] = [elementToAdd, ]


def flatten(listToFlattened):
    return [item for sublist in listToFlattened for item in sublist]


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

    def get(self, request, **kwargs):
        self._data = None
        self._request = request

    def post(self, request, **kwargs):
        self._data = json.loads(request.read().decode('utf-8').replace("'", "\""))
        self._request = request
        return self.post_method()

    def _get_data(self, key, default=None):
        if self._data:
            try:
                return self._data[key]
            except KeyError:
                return default
        else:
            return self._request.GET.get(key, default)

    def _get_data_or_error(self, key, error=HttpResponseBadRequest):
        if self._data:
            try:
                return self._data[key]
            except KeyError:
                raise error
        else:
            data = self._request.GET.get(key, None)
            if not data:
                raise error
            else:
                return data
