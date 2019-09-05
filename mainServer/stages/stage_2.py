import base64
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponseBadRequest
from django.views import View

from mainServer.stages.JsonView import JsonView
from mainServer.stages.auxiliaryMethods import *
from django.http import HttpResponse
from scipy.interpolate import interp1d
import json
from functools import reduce
from django.core.exceptions import ObjectDoesNotExist


@method_decorator(csrf_exempt, name='dispatch')
class NextMovie(JsonView):
    def get_method(self):
        sessionId = self.get_data_or_error("sessionId")

        previousMovieId = self.get_data("previousMovieId", None)
        if previousMovieId:
            previousMovie = Film.objects.get(pk=previousMovieId)
            statusToAdd = StatusFilmu.objects.get(status="Przypisano punkty")
            removeMultipleStatuses(previousMovie, ["W trakcie obslugi", "Przetworzono"])
            previousMovie.status.add(statusToAdd)
            previousMovie.save()

        try:
            nextMovie = Film.objects \
                .filter(sesja__pk=sessionId, status__status__in=["Przetworzono"]) \
                .order_by("data")[0]
            statusToAdd = StatusFilmu.objects.get(status="W trakcie obslugi")
            nextMovie.status.add(statusToAdd)
        except IndexError:
            movieCount = Film.objects \
                .filter(sesja__pk=sessionId, status__status__in=["W trakcie przetwarzania", "Do przetworzenia"]) \
                .count()

            if movieCount:
                return JsonResponse({"count": movieCount}, status=400)
            else:
                return HttpResponse(status=404)

        return JsonResponse({
            "movieId": nextMovie.pk,
            "framesCount": nextMovie.iloscKlatek,
            "fps": nextMovie.FPS,
            "name": nextMovie.nazwa,
            "x": nextMovie.rozmiarX,
            "y": nextMovie.rozmiarY,
        })


@method_decorator(csrf_exempt, name='dispatch')
class Frame(JsonView):
    def get_method(self):
        movieId = self.get_data_or_error("movieId")
        frameNr = self.get_data_or_error("frameNr")
        imagePath = Klatka.objects.get(film__pk=movieId, nr=frameNr).getPath()
        try:
            wrapper = base64.b64encode(open(imagePath, 'rb').read()).decode('utf-8')
        except FileNotFoundError as e:
            raise Http404(str(e))

        response = HttpResponse(wrapper, content_type='image/png')
        return response


@method_decorator(csrf_exempt, name='dispatch')
class FramePosition(View):

    def get(self, request, **kwargs):
        movieId = request.GET.get('movieId', False)
        frameNr = request.GET.get("frameNr", False)
        if movieId and frameNr:
            frame = Klatka.objects.get(film__pk=movieId, nr=frameNr)
            positionObjects = PozycjaPunktu.objects.filter(klatka=frame)
            frameId = frame.pk
        else:

            frameId = request.GET.get("frameId", False)
            if frameId:
                positionObjects = PozycjaPunktu.objects.filter(klatka__pk=frameId)
            else:
                return HttpResponseBadRequest()

        positions = self.positionsAsDict(positionObjects)
        if positions:
            return JsonResponse({"positions": positions, "frameId": frameId})
        else:
            return JsonResponse({"frameId": frameId})

    def post(self, request, **kwargs):
        try:
            data = json.loads(request.read().decode('utf-8'))

            frameId = data["frameId"]
            frameObject = Klatka.objects.get(pk=frameId)

            colorSetObject = frameObject.film.sesja.zbiorKolorow
            colorObjects = Kolor.objects.filter(zbiorkolorow=colorSetObject)
            colors = {colorObject.nazwa for colorObject in colorObjects}

            if "color" in data:
                color = data["color"]
                if color not in colors:
                    raise HttpResponseBadRequest

                colorObject = Kolor.objects.get(nazwa=color)
            else:
                if colorSetObject.domyslny_kolor is not None:
                    colorObject = colorSetObject.domyslny_kolor
                else:
                    colorObject = Kolor.objects.get(nazwa=colors.pop())

            status = data["status"]

            if not status == noObjectPositionStatus:
                position = data["position"]
                x = position["x"]
                y = position["y"]

        except KeyError:
            raise HttpResponseBadRequest
        except:
            raise Http404

        if not status == noObjectPositionStatus:
            position = self._addPosition(colorObject, status, frameObject, x, y)
        else:
            position = self._addPosition(colorObject, status, frameObject)

        if status == endPositionStatus:
            self.addInterpolationPosition(frameObject, colorObject)

        return JsonResponse({"positionId": position[0].pk})

    def delete(self, request, **kwargs):
        try:
            data = json.loads(request.read().decode('utf-8'))
            positionId = data["positionId"]
            positionObject = PozycjaPunktu.objects.get(pk=positionId)
            deleted = positionObject.delete()
            if deleted.count() != 0:
                raise Http404
        except:
            raise Http404

        return JsonResponse({"ok": "ok"})

    @staticmethod
    def _addPosition(color: str, status: str, frameObject, x: int = None, y: int = None):
        statusObject = StatusPozycji.objects.get(status=status)  # TODO: obsługa błedu

        replacedStatuses = [userPositionStatus, endPositionStatus, noObjectPositionStatus]
        if status in replacedStatuses:
            statusObjects = [
                StatusPozycji.objects.get(status=replacedStatus) for replacedStatus in replacedStatuses
            ]
        else:
            statusObjects = [statusObject]

        colorSetObject = frameObject.film.sesja.zbiorKolorow
        colorObjects = Kolor.objects.filter(zbiorkolorow=colorSetObject)
        colors = {colorObject for colorObject in colorObjects}

        if color not in colors:
            raise RuntimeError("Color not in color set")

        position = PozycjaPunktu.objects.update_or_create(
            klatka=frameObject,
            kolor=color,
            status__in=statusObjects,
            defaults={
                "x": x,
                "y": y,
                "status": statusObject,
                "kolor": color,
            }
        )
        return position

    @staticmethod
    def positionsAsDict(positions):
        if positions is None:
            return None
        if len(positions) > 0:
            positionsArray = [
                {
                    "x": position.x,
                    "y": position.y,
                    "status": position.status.status,
                    "color": position.kolor.nazwa if position.kolor else None,
                    "color_code": position.kolor.kod if position.kolor else None,
                    "id": position.pk,
                } if position else None

                for position in positions
            ]
            return positionsArray
        else:
            return False

    @staticmethod
    def xsAndYsFromDicts(dictions):
        if dictions is None:
            return None
        return zip(*[(dictElement["x"], dictElement["y"]) if dictElement else (None, None)
                     for dictElement in dictions])

    @classmethod
    def positionsXYInfo(cls, positionObjects):
        positionDicts = cls.positionsAsDict(positionObjects)

        def toReduceSplitByEndStatus(ret, positionDict):  # second index its cache
            ret[1].append({
                "x": positionDict["x"],
                "y": positionDict["y"]
            })
            if positionDict["status"] == endPositionStatus:  # or len(ret[1]) == 0
                ret[0].append(ret[1][:])
                ret[1] = []

            return ret

        splitedByEndStatus = list(reduce(toReduceSplitByEndStatus, positionDicts, ([], [])))[0]
        xs, ys = [cls.xsAndYsFromDicts(dicts) for dicts in splitedByEndStatus]
        return xs, ys

    @staticmethod
    def findLastFrameWithEndStatusOrNone(frame):
        movieId = frame.film.pk
        ordererFramesWithEndStatus = Klatka.objects \
            .filter(film__pk=movieId, nr__lt=frame.nr, pozycja__status__status__in=[endPositionStatus, ]) \
            .order_by("nr")
        try:
            return ordererFramesWithEndStatus.last()
        except:
            try:
                return ordererFramesWithEndStatus[0]
            except:
                return None

    @classmethod
    def findStartFrame(cls, frame, colorObject):
        lastEndFrame = cls.findLastFrameWithEndStatusOrNone(frame)
        lastEndFrameNr = lastEndFrame.nr if lastEndFrame else 0

        userFramesAfterLastEndFrame = Klatka.objects\
            .filter(film=frame.film, nr__gt=lastEndFrameNr,
                    pozycja__status__status=userPositionStatus, pozycja__kolor=colorObject)\
            .order_by("nr")
        startFrame = userFramesAfterLastEndFrame[0]

        return startFrame

    @classmethod
    def findAllFramesFromStartToEnd(cls, frame, colorObject):
        startFrame = cls.findStartFrame(frame, colorObject)
        return Klatka.objects.filter(film=startFrame.film, nr__gte=startFrame.nr, nr__lte=frame.nr)

    @classmethod
    def userPositionsXsYsInfo(cls, framesFromStartToEnd, colorObject):
        def getPosition(frame):
            try:
                return PozycjaPunktu.objects.get(
                    klatka=frame, kolor=colorObject,
                    status__status__in=[userPositionStatus, endPositionStatus, noObjectPositionStatus]
                )
            except ObjectDoesNotExist:
                return None

        positions = []
        withoutPoint = []
        isAfterNoObjectPositionStatus = False

        for frame in framesFromStartToEnd:
            position = getPosition(frame)

            if isAfterNoObjectPositionStatus:
                withoutPoint.append(frame)
            else:
                if position and position.status.status == noObjectPositionStatus:
                    isAfterNoObjectPositionStatus = True
                    withoutPoint.append(frame)
                else:
                    positions.append(position)

        xs, ys = cls.xsAndYsFromDicts(cls.positionsAsDict(positions))
        return xs, ys, withoutPoint

    @staticmethod
    def interpolate(xs):
        itsXs = [[it, x] for it, x in enumerate(xs)]
        itsXs = [el for el in itsXs if el[1] is not None]
        its, xsNotNone = list(zip(*itsXs))
        f = interp1d(its, xsNotNone, kind='quadratic', bounds_error=False, fill_value='extrapolate')
        return f(range(len(xs)))

    @classmethod
    def addInterpolationPosition(cls, frame, colorObject):
        frames = cls.findAllFramesFromStartToEnd(frame, colorObject)
        xs, ys, withoutPoint = cls.userPositionsXsYsInfo(frames, colorObject)

        interpolatedXs = cls.interpolate(xs)
        interpolatedYs = cls.interpolate(ys)

        for x, y, frame in zip(interpolatedXs, interpolatedYs, frames):
            cls._addPosition(colorObject, interpolatedPositonStatus, frame, x, y)

        for frame in withoutPoint:
            cls._addPosition(colorObject, noObjectPositionStatus, frame)
