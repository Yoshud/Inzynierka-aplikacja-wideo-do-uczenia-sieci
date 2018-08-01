from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import Http404, HttpResponseServerError
from mainServer.skryptyEtapy.helpersMethod import *
import json
import os
from functools import reduce
from time import sleep
import numpy as np


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
            try:
                dataAugmentationFolderPath = data["toSaveFolderPath"]
            except KeyError:
                now = timezone.now()
                folderName = "{}_dataAugmentation_{}_{}" \
                    .format(session.nazwa, now.date(), now.time()) \
                    .replace(":", "_").replace(".", "_")
                dataAugmentationFolderPath = os.path.join(os.path.join(pathUp(currentPath()), 'ObrazyGotowe'),
                                                          folderName)
            framesId = flatten([self.getMovieFrameIds(movieId) for movieId in moviesId])

            for frameId in framesId:
                self.addOrder(frameId, dataAugmentationCode, dataAugmentationFolderPath, expectedSize)
                sleep(0.1)
            return JsonResponse({"folderPath": dataAugmentationFolderPath})
        except:
            raise Http404

    def orderToDict(self, dataAugmenationOrder):
        positionObject = self.getUserPositionOr404(dataAugmenationOrder.klatka)
        position = (positionObject.pozycjaX, positionObject.pozycjaY)
        expectedSize = (dataAugmenationOrder.oczekiwanyRozmiarX, dataAugmenationOrder.oczekiwanyRozmiarY)
        orderDict = {
            "frameId": dataAugmenationOrder.klatka.pk,
            "augmentationCode": dataAugmenationOrder.kodAugmentacji,
            "framePath": dataAugmenationOrder.klatka.sciezka,
            "pathToSave": dataAugmenationOrder.folder.sciezka,
            "pointPosition": position,
            "expectedSize": expectedSize,
        }
        dataAugmenationOrder.wTrakcie = True
        dataAugmenationOrder.save()
        return orderDict

    def getMovieFrameIds(self, movieId):
        frames = Klatka.objects.filter(film__pk=movieId)
        return [frame.pk for frame in frames]

    def addOrder(self, frameId, dataAugmentationCode, dataAugmentationFolderPath, expectedSize):
        folder = FolderZPrzygotowanymiObrazami.objects.create(sciezka=dataAugmentationFolderPath)
        ZlecenieAugmentacji.objects.create(
            klatka_id=frameId,
            kodAugmentacji=dataAugmentationCode,
            folder=folder,
            oczekiwanyRozmiarX=expectedSize["x"], oczekiwanyRozmiarY=expectedSize["y"]
        )

    def getUserPositionOr404(self, frame):
        try:
            return PozycjaPunktu.objects.get(klatka=frame,
                                             status__status__in=[userPositionStatus, endPositionStatus])
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
        except:
            raise Http404
        try:
            self.addImage(pointPosition, cropPosition, resizeScale, frameId, toImagePath, methodCode)
        except:
            raise HttpResponseServerError
        return JsonResponse({"ok": True})

    def addImage(self, pointPosition, cropPosition, resizeScale, frameId, toImagePath, methodCode):
        status = StatusPozycjiCrop.objects.get_or_create(status="punktOrginalny")[0]
        cropPositionObject = PozycjaCropa.objects.create(pozycjaX=int(cropPosition[0]), pozycjaY=int(cropPosition[1]))
        image = ObrazPoDostosowaniu.objects.create(
            pozycjaCropa=cropPositionObject,
            wspResize=resizeScale,
            klatkaMacierzysta_id=frameId,
            sciezka=toImagePath,
            metoda=methodCode
        )

        PozycjaPunktuPoCrop.objects.create(
            obraz=image, status=status,
            pozycjaX=int(float(pointPosition[0])), pozycjaY=int(float(pointPosition[1]))
        )
