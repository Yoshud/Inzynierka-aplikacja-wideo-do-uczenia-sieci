from mainServer.models import *
import os
from os import walk
from django.http import Http404
from pathlib import Path

imagesFolderName = "Obrazy"
modelsFolderName = "Modele"
processedFolderName = "Przygotowane"

endPositionStatus = "Koniec"
userPositionStatus = "Dodane uzytkownik"
interpolatedPositonStatus = "Interpolacja"
noObjectPositionStatus = "Brak"


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
