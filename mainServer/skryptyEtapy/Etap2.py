from django.shortcuts import render
from django.http import HttpResponse
import os
from functools import reduce
from django.views.generic import View
from os import walk
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import Http404, HttpResponseServerError
import cv2
import datetime
from mainServer.models import *
from django.utils import timezone


@method_decorator(csrf_exempt, name='dispatch')
class ReturnMoviesToProcess(View):
    def addMovieToMoviesDict(self, movie,
                             statusToRemove=StatusFilmu.objects.get(status="Do przetworzenia"),
                             statusToAdd=StatusFilmu.objects.get(status="W trakcie przetwarzania")):
        movie.status.remove(statusToRemove)
        movie.status.add(statusToAdd)
        return {
            "path": movie.sciezka,
            "id": movie.pk,
            "pathToSave": movie.sesja.folderZObrazami.sciezka
        }
    def post(self, request, **kwargs):
        movies = Film.objects \
            .filter(status__status__in=["Do przetworzenia"])
        moviesDict = [self.addMovieToMoviesDict(movie) for movie in movies]
        return JsonResponse({
            "movies": moviesDict,
        })
# class GetSessionId(View):
#     def post(self, request, **kwargs):
#         movies = Film.objects \
#             .filter(status__status__in=["Do przetworzenia"])
#         pathToSave = Sesja.objects.get(pk=request.session["sessionPk"]).folderZObrazami.sciezka
#         moviesDict = [self.addMovieToMoviesDict(movie) for movie in movies]
#         return JsonResponse({
#             "movies": moviesDict,
#             "pathToSave": pathToSave,
#         })

@method_decorator(csrf_exempt, name='dispatch')
class MovieProcessed(View):
    def addToProcessedMovies(self, movie,
                             statusToRemove=StatusFilmu.objects.get(status="W trakcie przetwarzania"),
                             statusToAdd=StatusFilmu.objects.get(status="Przetworzono")):
        movie.status.remove(statusToRemove)
        movie.status.add(statusToAdd)
        print(movie.nazwa)
    # def post(self, request, **kwargs):
    #     ids = request.POST.getlist("movieId")
    #     if ids == []:
    #         raise Http404
    #     for id in ids:
    #         try:
    #             self.addToProcessedMovies(Film.objects.get(pk=id))
    #         except:
    #             raise HttpResponseServerError
    #     return JsonResponse({"ok": True})
    def post(self, request, **kwargs):
        id = request.POST.get("movieId")
        if id == -1:
            raise Http404
        try:
            self.addToProcessedMovies(Film.objects.get(pk=id))
        except:
            raise HttpResponseServerError
        return JsonResponse({"ok": True})