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
            if numberOfRandomCrops > 10:
                numberOfRandomCrops = 9
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
                self.addOrder(frameId, dataAugmentationCode, dataAugmentationFolderPath)
                sleep(0.1)
            return JsonResponse({"folderPath": dataAugmentationFolderPath})
        except:
            raise Http404

    def orderToDict(self, dataAugmenationOrder):
        ordersDict = {
            "frameId": dataAugmenationOrder.klatka.pk,
            "augmentationCode": dataAugmenationOrder.kodAugmentacji,
            "framePath": dataAugmenationOrder.klatka.sciezka,
            "pathToSave": dataAugmenationOrder.folder.sciezka,
        }
        dataAugmenationOrder.wTrakcie = True
        dataAugmenationOrder.save()
        return ordersDict

    def getMovieFrameIds(self, movieId):
        frames = Klatka.objects.filter(film__pk=movieId)
        return [frame.pk for frame in frames]

    def addOrder(self, frameId, dataAugmentationCode, dataAugmentationFolderPath):
        folder = FolderZPrzygotowanymiObrazami.objects.create(sciezka=dataAugmentationFolderPath)
        ZlecenieAugmentacji.objects.create(klatka__pk=frameId, kodAugmentacji=dataAugmentationCode, folder=folder)


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
        image = ObrazPoDostosowaniu.objects.create(
            pozycjaCropa=cropPosition,
            wspResize=resizeScale,
            klatkaMacierzysta__pk=frameId,
            sciezka=toImagePath,
            metoda=methodCode
        )

        PozycjaPunktuPoCrop.objects.create(
            obraz=image, status=status,
            pozycjaX=pointPosition[0], pozycjaY=pointPosition[1]
        )
