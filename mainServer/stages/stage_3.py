from collections import defaultdict
from functools import reduce

import numpy as np
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.http import HttpResponseServerError

from mainServer.stages.JsonView import JsonView
from mainServer.stages.auxiliaryMethods import *
import json


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
        sessionId = data["sessionId"]
        session = Sesja.objects.get(pk=sessionId)
        moviesId = data["moviesId"]
        isFlipVertical = 1 if data["isFlipVertical"] else 0
        isFlipHorizontal = 1 if data["isFlipHorizontal"] else 0
        numberOfRandomCrops = int(data["numberOfRandomCrops"])

        if numberOfRandomCrops > 10:
            numberOfRandomCrops = 9
        if numberOfRandomCrops < 1:
            numberOfRandomCrops = 1
        dataAugmentationCode = 1000 + 100 * isFlipVertical + 10 * isFlipHorizontal + numberOfRandomCrops

        if "toSaveFolderPath" in data:
            dataAugmentationFolder = FolderZPrzygotowanymiObrazami(sciezka=data["toSaveFolderPath"])
        else:
            now = timezone.now()
            folderName = "dataAugmentation_{}_{}" \
                .format(now.date(), now.time()) \
                .replace(":", "_").replace(".", "_")
            dataAugmentationFolder = FolderZPrzygotowanymiObrazami.objects.create(sesja=session, nazwa=folderName)

        frames = flatten([self.getMovieFrames(movieId) for movieId in moviesId])

        for frame in frames:
            self.addOrder(frame, dataAugmentationCode, dataAugmentationFolder)

        return JsonResponse({"folderPath": dataAugmentationFolder.getPath()})

    def orderToDict(self, dataAugmenationOrder):
        positionObjects = self.getInterpolatedAndNoObjectPositionsOr404(dataAugmenationOrder.klatka)
        positions = {
            positionObject.kolor.nazwa: positionObject.getPosition()
            for positionObject in positionObjects
        }

        orderDict = {
            "frameId": dataAugmenationOrder.klatka.pk,
            "augmentationCode": dataAugmenationOrder.kodAugmentacji,
            "framePath": dataAugmenationOrder.klatka.getPath(),
            "pathToSave": dataAugmenationOrder.folder.getPath(),
            "pointPositions": positions,
            "orderId": dataAugmenationOrder.pk,
        }
        dataAugmenationOrder.wTrakcie = True
        dataAugmenationOrder.save()

        return orderDict

    @staticmethod
    def getMovieFrames(movieId):
        frames = Klatka.objects.filter(
            film__pk=movieId,
            pozycja__status__status__in=[interpolatedPositonStatus]
        ).distinct()
        return frames

    @staticmethod
    def addOrder(frame, dataAugmentationCode, dataAugmentationFolder):
        augmentationOrderCountForFrame = ZlecenieAugmentacji.objects \
            .filter(klatka=frame) \
            .count()
        noAugmentationOrderForFrame = (augmentationOrderCountForFrame == 0)

        if noAugmentationOrderForFrame:
            # folder = FolderZPrzygotowanymiObrazami.objects.get_or_create(sciezka=dataAugmentationFolderPath)[0]
            ZlecenieAugmentacji.objects.create(
                klatka=frame,
                kodAugmentacji=dataAugmentationCode,
                folder=dataAugmentationFolder,
            )

    @staticmethod
    def getInterpolatedAndNoObjectPositionsOr404(frame):
        try:
            return PozycjaPunktu.objects.filter(
                klatka=frame,
                status__status__in=[interpolatedPositonStatus, noObjectPositionStatus]
            )
        except ObjectDoesNotExist:
            return Http404
        except:
            return HttpResponseServerError


# internal
@method_decorator(csrf_exempt, name='dispatch')
class ImageAfterDataAugmentation(JsonView):
    def post_method(self):

        pointPositions = self.get_data_or_error("pointPositions")
        cropPosition = self.get_data_or_error("cropPosition")
        frameId = self.get_data_or_error("frameId")
        imageName = self.get_data_or_error("imageName")
        methodCode = self.get_data_or_error("methodCode")
        orderId = self.get_data_or_error("orderId")

        self.addImage(pointPositions, cropPosition, frameId, imageName, methodCode, orderId)
        return JsonResponse({"ok": True})

    @staticmethod
    def addImage(pointPositions, cropPosition, frameId, imageName, methodCode, orderId):
        cropPositionObject = PozycjaCropa.objects.create(x=int(cropPosition[0]), y=int(cropPosition[1]))
        image = ObrazPoDostosowaniu.objects.create(
            pozycjaCropa=cropPositionObject,
            klatkaMacierzysta_id=frameId,
            nazwa=imageName,
            metoda=methodCode,
            zlecenie_id=orderId,
        )

        PozycjaPunktuPoCrop.objects.create(
            obraz=image, json=json.dumps(pointPositions)
        )


@method_decorator(csrf_exempt, name='dispatch')
class DivideIntoSets(JsonView):
    def post_method(self):
        dataSetsRatios = self.get_data_or_error("dataSetRatios")
        sessionId = self.get_data_or_error("sessionId")

        if sum(dataSetsRatios) != 1.0 or (0 > len(dataSetsRatios) > 3):
            raise HttpResponseBadRequest

        dataSetObjectPk = self.divideImagesIntoSets(sessionId, dataSetsRatios)

        return JsonResponse({"dataSetId": dataSetObjectPk})

    @staticmethod
    def divideImagesIntoSets(sessionId, dataSetsRatios):
        try:
            allImagesObjects = ObrazPoDostosowaniu.objects.filter(
                klatkaMacierzysta__film__sesja_id=sessionId,
            )
            allImagesObjects = np.random.permutation(allImagesObjects)

            def tmpFun(imagesAndRatioBefore, ratioAct):
                ratioEnd = ratioAct + imagesAndRatioBefore[1]
                start = int(len(allImagesObjects) * imagesAndRatioBefore[1])
                end = int(len(allImagesObjects) * ratioEnd)
                imagesAndRatioBefore[0].append(allImagesObjects[start:end])
                return imagesAndRatioBefore[0], ratioEnd

            dataSetsContent = reduce(tmpFun, dataSetsRatios, [[], 0.0])[0]
        except:
            raise Http404
        try:
            dataSetObject = ZbioryDanych.objects.create(sesja_id=sessionId)
            objectDataSets = [dataSetObject.uczacy, dataSetObject.testowy, dataSetObject.walidacyjny]

            for dataSetContent, dataSetField in zip(dataSetsContent, objectDataSets):
                dataSetField.add(*dataSetContent)

            dataSetObject.save()
        except:
            raise HttpResponseServerError

        return dataSetObject.pk


@method_decorator(csrf_exempt, name='dispatch')
class AugmentationProcessStatus(JsonView):
    def get_method(self):
        sessionId = self.get_data_or_error("sessionId")
        allSessionMovies = Film.objects.filter(sesja__pk=sessionId, status__status="Przypisano punkty")
        movieAugmentationStatuses = [self._movieAugmentationStatus(movie) for movie in allSessionMovies]
        return JsonResponse({"movies": movieAugmentationStatuses})

    @classmethod
    def _movieAugmentationStatus(cls, movie):
        frames = Klatka.objects.filter(film=movie, pozycja__status__status=interpolatedPositonStatus)
        frameOrderDict = defaultdict(lambda: defaultdict(list))
        for frame in frames:
            cls.addFrame(frame, frameOrderDict)
        a = {str(size): cls.movieProcessedStatus(framesDict, size) for size, framesDict in frameOrderDict.items()}
        return a

    @staticmethod
    def addFrame(frame, frameOrderDict):
        orders = ZlecenieAugmentacji.objects.filter(klatka=frame)
        for order in orders:
            frameOrderDict[(order.oczekiwanyRozmiarX, order.oczekiwanyRozmiarY)][frame].append(order.kodAugmentacji)

    @classmethod
    def movieProcessedStatus(cls, framesDict, size):
        numberOfProcessedFrames = sum(
            [
                int(cls.isFrameProcessed(frame, augmentationCodes, size))
                for frame, augmentationCodes in framesDict.items()
            ]
        )
        return numberOfProcessedFrames / len(framesDict.values())

    @classmethod
    def isFrameProcessed(cls, frame, augmentationCodes, size):
        expectedNumberOfImages = sum(map(cls.numberOfImagesAfterAugmentation, augmentationCodes))
        numberOfImages = ObrazPoDostosowaniu.objects \
            .filter(klatkaMacierzysta=frame,
                    zlecenie__oczekiwanyRozmiarX=size[0],
                    zlecenie__oczekiwanyRozmiarY=size[1])\
            .count()

        return expectedNumberOfImages == numberOfImages

    @staticmethod
    def numberOfImagesAfterAugmentation(augmentationCode):
        augmentationCode = str(augmentationCode)
        return (1 + int(augmentationCode[1]) + int(augmentationCode[2])) * int(augmentationCode[3])
