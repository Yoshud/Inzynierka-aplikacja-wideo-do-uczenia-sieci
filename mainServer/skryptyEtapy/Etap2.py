from django.views.generic import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import Http404, HttpResponseServerError
from mainServer.models import *
import json


@method_decorator(csrf_exempt, name='dispatch')
class ReturnMoviesToProcess(View):
    def addMovieToMoviesDict(self, movie,
                             statusToRemove=StatusFilmu.objects.get(status="Do przetworzenia"),
                             statusToAdd=StatusFilmu.objects.get(status="W trakcie przetwarzania")):
        movie.status.remove(statusToRemove)
        movie.status.add(statusToAdd)
        return {
            "path": movie.sciezka,
            "movieName": movie.nazwa,
            "id": movie.pk,
            "pathToSave": movie.sesja.folderZObrazami.sciezka,
        }

    def post(self, request, **kwargs):
        movies = Film.objects \
                     .filter(status__status__in=["Do przetworzenia"])[:5]
        moviesDict = [self.addMovieToMoviesDict(movie) for movie in movies]
        return JsonResponse({
            "movies": moviesDict,
        })


@method_decorator(csrf_exempt, name='dispatch')
class MovieProcessed(View):
    def addToProcessedMovies(self, movie, frames,
                             statusToRemove=StatusFilmu.objects.get(status="W trakcie przetwarzania"),
                             statusToAdd=StatusFilmu.objects.get(status="Przetworzono")):
        movie.status.remove(statusToRemove)
        movie.status.add(statusToAdd)
        for frameInfo in frames:
            frame = Klatka(sciezka=frameInfo["path"], nr=frameInfo["nr"], film=movie)
            frame.save()
        print(movie.nazwa)

    def post(self, request, **kwargs):
        data = json.loads(request.read().decode('utf-8').replace("'", "\""))
        movieId = data.get("movieId", False)
        frames = data["frames"]
        try:
            self.addToProcessedMovies(Film.objects.get(pk=movieId), frames)
        except:
            raise HttpResponseServerError
        return JsonResponse({"ok": True})
