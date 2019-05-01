import json
from functools import wraps
from django.http import HttpResponseBadRequest, HttpResponseServerError
from mainServer.models import *
import os
from os import walk
from django.http import Http404
from django.views.generic import View
from abc import ABC, abstractmethod
from pathlib import Path

imagesFolderName = "Obrazy"
modelsFolderName = "Modele"
processedFolderName = "Przygotowane"

endPositionStatus = "Koniec"
userPositionStatus = "Dodane uzytkownik"
interpolatedPositonStatus = "Interpolacja"
noObjectPositionStatus = "Brak"


class MyError(Exception):
    def __init__(self, errorClass):
        self.errorClass = errorClass


def django_exceptions(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        try:
            return view_func(*args, **kwargs)
        except MyError as e:
            return e.errorClass
        except Exception as e:
            return HttpResponseServerError(str(e))

    return wrapper


def filterFilms(files):
    filmSufixes = [".mp4", ".avi", ".mpeg", ".mpg", ".h264"]
    return list(filter(lambda file: any([sufix in file for sufix in filmSufixes]), files))


def filterImages(files):
    imageSufixes = [".jpg", ".png"]
    return list(filter(lambda file: any([sufix in file for sufix in imageSufixes]), files))


def validateReturnForPath(folders):
    if folders == None:
        raise Http404


def foldersAndMovieFilesFromPath(path):
    _, foldernames, filenames = next(walk(path), (None, None, []))
    validateReturnForPath(foldernames)
    filenames = filterFilms(filenames)
    return foldernames, filenames


def imagesFileNamesFromPath(path):
    _, foldernames, filenames = next(walk(path), (None, None, []))
    validateReturnForPath(foldernames)
    filenames = filterImages(filenames)
    return filenames, path


def pathUp(path):
    return os.path.dirname(path)


def currentPath():
    return os.getcwd()


def createDirPath(path):
    pathToCreate = Path(path)
    pathToCreate.mkdir(parents=True, exist_ok=True)


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

    def _get_data(self, key, default=None):
        if self._data:
            try:
                return self._data[key]
            except KeyError:
                return default
        else:
            return self._request.GET.get(key, default)

    def _get_data_or_error(self, key, error=HttpResponseBadRequest()):
        if self._data:
            if key in self._data:
                return self._data[key]
            else:
                raise MyError(error)
        else:
            data = self._request.GET.get(key, None)
            if not data:
                raise MyError(error)
            else:
                return data
