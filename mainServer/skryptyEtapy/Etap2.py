from django.views.generic import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import Http404, HttpResponseServerError
from mainServer.models import *
from wsgiref.util import FileWrapper
from django.http import HttpResponse
import json
import os


def getMultipleMovieStatuses(statuses):
    return [StatusFilmu.objects.get_or_create(status=status)[0]
            for status in statuses]


def removeMultipleStatuses(movie, statuses):
    for status in getMultipleMovieStatuses(statuses):
        movie.status.remove(status)


@method_decorator(csrf_exempt, name='dispatch')
class ReturnMoviesToProcess(View):
    def addMovieToMoviesDict(self, movie,
                             statusToRemove=StatusFilmu.objects.get_or_create(status="Do przetworzenia")[0],
                             statusToAdd=StatusFilmu.objects.get_or_create(status="W trakcie przetwarzania")[0]):
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
                             statusToRemove=StatusFilmu.objects.get_or_create(status="W trakcie przetwarzania")[0],
                             statusToAdd=StatusFilmu.objects.get_or_create(status="Przetworzono")[0]):
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


@method_decorator(csrf_exempt, name='dispatch')
class GetNextMovie(View):
    def post(self, request, **kwargs):
        data = json.loads(request.read().decode('utf-8'))
        try:
            sessionId = data["sessionId"]
        except:
            raise Http404
        try:
            previousMovieId = data["previousMovieId"]

            previousMovie = Film.objects.get(pk=previousMovieId)
            statusToAdd = StatusFilmu.objects.get_or_create(status="Przypisano punkty")[0]
            removeMultipleStatuses(previousMovie, ["W trakcie obslugi", "Przetworzono"])
            previousMovie.status.add(statusToAdd)
            previousMovie.save()
        except KeyError:
            pass
        except:
            raise HttpResponseServerError
        finally:
            try:
                nextMovie = Film.objects \
                    .filter(sesja__pk=sessionId, status__status__in=["Przetworzono"]) \
                    .order_by("data")[0]
                statusToAdd = StatusFilmu.objects.get_or_create(status="W trakcie obslugi")[0]
                nextMovie.status.add(statusToAdd)
            except IndexError:
                movieCount = Film.objects \
                    .filter(sesja__pk=sessionId, status__status__in=["W trakcie przetwarzania"]).count()
                if movieCount:
                    return JsonResponse({"count": movieCount})
                else:
                    raise Http404
        return JsonResponse({"movieId": nextMovie.pk})


@method_decorator(csrf_exempt, name='dispatch')
class GetFrame(View):
    def post(self, request, **kwargs):
        data = json.loads(request.read().decode('utf-8'))
        movieId = data.get("movieId")
        frameNr = data.get("frameNr")
        imagePath = Klatka.objects.get(film__pk=movieId, nr=frameNr).sciezka
        wrapper = FileWrapper(open(os.path.abspath(imagePath), 'rb'))
        response = HttpResponse(wrapper, content_type='image/jpg')
        response['Content-Disposition'] = 'attachment; imageName=%s' % os.path.basename(imagePath)
        response['Content-Length'] = os.path.getsize(imagePath)
        return response


@method_decorator(csrf_exempt, name='dispatch')
class GetFramePositions(View):
    def positionsAsJsonDict(self, positions):
        if len(positions) > 0:
            positionsArray = [{
                "x": position.pozycjaX,
                "y": position.pozycjaY,
                "status": position.status.status,
            } for position in positions]
            return {"positions": positionsArray,
                    "frameId": positions[0].klatka.pk,
                    }
        else:
            return {}

    def post(self, request, **kwargs):
        def post(self, request, **kwargs):
            data = json.loads(request.read().decode('utf-8'))
            try:
                movieId = data["movieId"]
                frameNr = data["frameNr"]
                positionObjects = PozycjaPunktu.objects.filter(klatka__film__pk=movieId, klatka__nr=frameNr)
            except TypeError:
                try:
                    frameId = data.get("frameId")
                    positionObjects = PozycjaPunktu.objects.filter(klatka__pk=frameId)
                except:
                    raise Http404
            finally:
                return JsonResponse(self.positionsAsJsonDict(positionObjects))

@method_decorator(csrf_exempt, name='dispatch')
class AddPosition(View):
    def post(self, request, **kwargs):
        try:
            data = json.loads(request.read().decode('utf-8'))
            frameId = data["frameId"]
            position = data["position"]
            x = position["x"]
            y = position["y"]
            frameObject = Klatka.objects.get(pk=frameId)
        except:
            raise Http404
        try:
            status = request["status"]
        except TypeError:
            status = "Dodane uzytkownik"
        except:
            raise Http404
        finally:
            statusObject = StatusPozycji.objects.get_or_create(status=status)[0]
            position = PozycjaPunktu.objects.create(klatka=frameObject, status=statusObject, pozycjaX=x, pozycjaY=y)
            return JsonResponse({"positionId": position.pk})
