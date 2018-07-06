from django.shortcuts import render
from django.http import HttpResponse
import os
from functools import reduce
from django.views.generic import View
from os import walk
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import Http404
import cv2
import datetime
from django.utils import timezone

def validateReturnForPath(folders):
    if folders == None:
        raise Http404


def foldersAndFilesFromPath(path):
    _, foldernames, filenames = next(walk(path), (None, None, []))
    validateReturnForPath(foldernames)
    return foldernames, filenames


def pathUp(path):
    return os.path.dirname(path)


def currentPath():
    return os.getcwd()


@method_decorator(csrf_exempt, name='dispatch')
class GetObjectsFromPath(View):
    def get(self, request, **kwargs):
        path = request.GET.get('path', None)
        parent = request.GET.get('parent', None)
        child = request.GET.get('child', '')
        if path==None:
            raise Http404
        if parent != None:
            path = pathUp(path)
        else:
            if child != '':
                path = os.path.join(path, child)
        folders, files = foldersAndFilesFromPath(path)
        return JsonResponse({
            "currentDir": path,
            "folders": folders,
            "files": files,
        })

@method_decorator(csrf_exempt, name='dispatch')
class AddMovie(View):
    def get(self, request, **kwargs):
        path = request.GET.get('path', 'lastPath')
        cap = cv2.VideoCapture(path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        iloscKlatek = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        dlugosc = iloscKlatek/fps
        dlugosc = datetime.timedelta(seconds=dlugosc)
        x = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        y = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        return JsonResponse({
            "fps": fps,
            "iloscKlatek": int(iloscKlatek),
            "dlugosc": str(dlugosc),
            "x": int(x),
            "y": int(y),
        })
