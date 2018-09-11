from collections import defaultdict

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import Http404, HttpResponseServerError
from mainServer.skryptyEtapy.helpersMethod import *
import json
import os
from ModelML.optimizerMethod import *
from ModelML.lossMethod import *


@method_decorator(csrf_exempt, name='dispatch')
class DataAugmentationOrder(View):
    def get(self, request, **kwargs):
        orders = ZlecenieAugmentacji.objects.filter(wTrakcie=False).order_by("pk")[0:20]
        ordersDict = [self.orderToDict(order) for order in orders]
        return JsonResponse({
            "orders": ordersDict,
        })

    def post(self, request, **kwargs):
        data = json.loads(request.read().decode('utf-8').replace("'", "\""))
        try:
            sessionId = data["sessionId"]
            session = Sesja.objects.get(pk=sessionId)
            moviesId = data["moviesId"]
            isFlipVertical = 1 if data["isFlipVertical"] else 0
            isFlipHorizontal = 1 if data["isFlipHorizontal"] else 0
            numberOfRandomCrops = int(data["numberOfRandomCrops"])
            expectedSize = data["expectedSize"]
            if numberOfRandomCrops > 10:
                numberOfRandomCrops = 9
            if numberOfRandomCrops < 1:
                numberOfRandomCrops = 1
            dataAugmentationCode = 1000 + 100 * isFlipVertical + 10 * isFlipHorizontal + numberOfRandomCrops

            if "toSaveFolderPath" in data:
                dataAugmentationFolderPath = data["toSaveFolderPath"]
            else:
                processedPath = session.folderPrzetworzone.sciezka
                now = timezone.now()
                folderName = "dataAugmentation_{}_{}" \
                    .format(now.date(), now.time()) \
                    .replace(":", "_").replace(".", "_")
                dataAugmentationFolderPath = os.path.join(processedPath, folderName)
            frames = flatten([self.getMovieFrames(movieId) for movieId in moviesId])

            for frame in frames:
                self.addOrder(frame, dataAugmentationCode, dataAugmentationFolderPath, expectedSize)

            return JsonResponse({"folderPath": dataAugmentationFolderPath})
        except:
            raise Http404

    def orderToDict(self, dataAugmenationOrder):
        positionObject = self.getInterpolatedPositionOr404(dataAugmenationOrder.klatka)
        position = (positionObject.x, positionObject.y)
        expectedSize = (dataAugmenationOrder.oczekiwanyRozmiarX, dataAugmenationOrder.oczekiwanyRozmiarY)
        orderDict = {
            "frameId": dataAugmenationOrder.klatka.pk,
            "augmentationCode": dataAugmenationOrder.kodAugmentacji,
            "framePath": dataAugmenationOrder.klatka.sciezka,
            "pathToSave": dataAugmenationOrder.folder.sciezka,
            "pointPosition": position,
            "expectedSize": expectedSize,
            "orderId": dataAugmenationOrder.pk,
        }
        dataAugmenationOrder.wTrakcie = True
        dataAugmenationOrder.save()
        return orderDict

    def getMovieFrames(self, movieId):
        frames = Klatka.objects.filter(
            film__pk=movieId,
            pozycja__status__status__in=[endPositionStatus, userPositionStatus, interpolatedPositonStatus]
        ).distinct()
        return frames

    def addOrder(self, frame, dataAugmentationCode, dataAugmentationFolderPath, expectedSize):
        augmentationOrderCountForFrame = ZlecenieAugmentacji.objects \
            .filter(klatka=frame, oczekiwanyRozmiarX=expectedSize["x"], oczekiwanyRozmiarY=expectedSize["y"]) \
            .count()
        noAugmentationOrderForFrame = augmentationOrderCountForFrame == 0

        if noAugmentationOrderForFrame:
            folder = FolderZPrzygotowanymiObrazami.objects.get_or_create(sciezka=dataAugmentationFolderPath)[0]
            ZlecenieAugmentacji.objects.create(
                klatka=frame,
                kodAugmentacji=dataAugmentationCode,
                folder=folder,
                oczekiwanyRozmiarX=expectedSize["x"], oczekiwanyRozmiarY=expectedSize["y"]
            )

    def getInterpolatedPositionOr404(self, frame):
        try:
            return PozycjaPunktu.objects.get(
                klatka=frame,
                status__status__in=[interpolatedPositonStatus]
            )
        except ObjectDoesNotExist:
            return Http404
        except:
            return HttpResponseServerError


@method_decorator(csrf_exempt, name='dispatch')
class ImageAfterDataAugmentation(View):
    def post(self, request, **kwargs):
        try:
            data = json.loads(request.read().decode('utf-8').replace("'", "\""))
            pointPosition = data["pointPosition"]
            cropPosition = data["cropPosition"]
            resizeScale = data["resizeScale"]
            frameId = data["frameId"]
            toImagePath = data["toImagePath"]
            methodCode = data["methodCode"]
            orderId = data["orderId"]
        except:
            raise Http404
        try:
            self.addImage(pointPosition, cropPosition, resizeScale, frameId, toImagePath, methodCode, orderId)
        except:
            raise HttpResponseServerError
        return JsonResponse({"ok": True})

    def addImage(self, pointPosition, cropPosition, resizeScale, frameId, toImagePath, methodCode, orderId):
        status = StatusPozycjiCrop.objects.get_or_create(status="punktOrginalny")[0]
        cropPositionObject = PozycjaCropa.objects.create(x=int(cropPosition[0]), y=int(cropPosition[1]))
        image = ObrazPoDostosowaniu.objects.create(
            pozycjaCropa=cropPositionObject,
            wspResize=resizeScale,
            klatkaMacierzysta_id=frameId,
            sciezka=toImagePath,
            metoda=methodCode,
            zlecenie_id=orderId
        )

        PozycjaPunktuPoCrop.objects.create(
            obraz=image, status=status,
            x=int(float(pointPosition[0])), y=int(float(pointPosition[1]))
        )


@method_decorator(csrf_exempt, name='dispatch')
class NeuralNetworks(View):
    def get(self, request, **kwargs):
        networks = Sieci.objects.all()
        responseDict = {
            "networks": [self.networkToDict(network) for network in networks]
        }

        return JsonResponse(responseDict)

    @classmethod
    def networkToDict(cls, network):
        return {
            "x": network.inputSizeX,
            "y": network.inputSizeY,
            "name": "Network nr. {}".format(network.pk),
            "id": network.pk,
            "description": network.opisXML
        }


@method_decorator(csrf_exempt, name='dispatch')
class ParametersMethodsArguments(View):
    def get(self, request, **kwargs):
        return JsonResponse({
            "loss": self.lossMethodParameters(),
            "optimize": self.optymizeMethodParameters(),
        })

    @staticmethod
    def optymizeMethodParameters():
        return {
            key: {"requirements": methodObject.requirements, "optional": methodObject.optional}
            for key, methodObject in optimizeMethodDict.items()
        }

    @staticmethod
    def lossMethodParameters():
        return {
            key: {"parameters": methodObject.parameters}
            for key, methodObject in lossMethodDict.items()
        }


@method_decorator(csrf_exempt, name='dispatch')
class AugmentationProcessStatus(JsonView):
    def get_method(self):
        sessionId = self._get_data_or_error("sessionId")
        allSessionMovies = Film.objects.filter(sesja__pk=sessionId, status__status="Przypisano punkty")
        movieAugmentationStatuses = [self._movieAugmentationStatus(movie) for movie in allSessionMovies]
        return JsonResponse({"movies": movieAugmentationStatuses})

    def post_method(self):
        pass

    def _movieAugmentationStatus(self, movie):
        frames = Klatka.objects.filter(film=movie, pozycja__status__status=interpolatedPositonStatus)
        frameOrderDict = defaultdict(lambda: defaultdict(list))
        for frame in frames:
            self.addFrame(frame, frameOrderDict)
        a = {str(size): self.movieProcessedStatus(framesDict, size) for size, framesDict in frameOrderDict.items()}
        return a

    def addFrame(self, frame, frameOrderDict):
        orders = ZlecenieAugmentacji.objects.filter(klatka=frame)
        for order in orders:
            frameOrderDict[(order.oczekiwanyRozmiarX, order.oczekiwanyRozmiarY)][frame].append(order.kodAugmentacji)

    def movieProcessedStatus(self, framesDict, size):
        numberOfProcessedFrames = sum(
            [int(self.isFrameProcessed(frame, augmentationCodes, size)) for frame, augmentationCodes in framesDict.items()]
        )
        return numberOfProcessedFrames / len(framesDict.values())

    def isFrameProcessed(self, frame, augmentationCodes, size):
        expectedNumberOfImages = sum(map(self.numberOfImagesAfterAugmentation, augmentationCodes))
        numberOfImages = ObrazPoDostosowaniu.objects \
            .filter(klatkaMacierzysta=frame, zlecenie__oczekiwanyRozmiarX=size[0], zlecenie__oczekiwanyRozmiarY=size[1])\
            .count()
        return expectedNumberOfImages == numberOfImages

    def numberOfImagesAfterAugmentation(self, augmentationCode):
        augmentationCode = str(augmentationCode)
        return (1 + int(augmentationCode[1]) + int(augmentationCode[2])) * int(augmentationCode[3])
