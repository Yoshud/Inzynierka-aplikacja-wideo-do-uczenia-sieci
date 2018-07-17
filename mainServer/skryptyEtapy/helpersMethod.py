from mainServer.models import *
import os
from os import walk
from django.http import Http404

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
