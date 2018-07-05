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


def validateReturnForPath(folders):
    if folders == None:
        raise Http404


def foldersAndFilesFromPath(path):
    _, foldernames, filenames = next(walk(path), (None, None, []))
    validateReturnForPath(foldernames)
    return foldernames, filenames


def pathUp(path):
    return os.path.dirname(os.path.dirname(path))


def currentPath():
    return os.getcwd()


@method_decorator(csrf_exempt, name='dispatch')
class GetObjectsFromPath(View):

    def getRememberedPath(self, request):
        path = request.session.get('pathGlobal', currentPath())
        request.session['pathGlobal'] = path
        return path

    def addToPath(self, toAdd, request):
        return os.path.join(self.getRememberedPath(request), toAdd)

    def get(self, request, **kwargs):
        path = request.GET.get('path', 'lastPath')
        pathGlobal = self.getRememberedPath(request)
        path = pathGlobal if path == 'lastPath' else path
        folders, files = foldersAndFilesFromPath(path)
        return JsonResponse({
            "currentDir": pathGlobal,
            "folders": folders,
            "files": files,
        })

    def post(self, request, **kwargs):
        next = request.POST.get("next", "pathUp")
        pathGlobal = self.getRememberedPath(request)
        request.session['pathGlobal'] = pathUp(pathGlobal) if next == "pathUp" else self.addToPath(next, request)
        try:
            folders, files = foldersAndFilesFromPath(request.session['pathGlobal'])
        except Http404:
            request.session['pathGlobal'] = pathGlobal
            raise Http404
        return JsonResponse({
            "currentDir": request.session['pathGlobal'],
            "folders": folders,
            "files": files,
        })
