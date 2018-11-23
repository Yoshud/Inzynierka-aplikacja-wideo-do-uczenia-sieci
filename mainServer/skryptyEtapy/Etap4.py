from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import Http404, HttpResponseServerError, HttpResponseBadRequest
from pathlib import Path
from mainServer.skryptyEtapy.helpersMethod import *
import json
import os
from functools import reduce
import numpy as np


@method_decorator(csrf_exempt, name='dispatch')
class DivideIntoSets(View): #TODO: sprawdzic
    def post(self, request, **kwargs):
        data = json.loads(request.read().decode('utf-8').replace("'", "\""))
        try:
            dataSetsRatios = data["dataSetRatios"]
            sessionId = data["sessionId"]

            networkId = data["networkId"]
        except:
            raise HttpResponseBadRequest

        network = Sieci.objects.get(pk=networkId)
        imgSizeX = network.inputSizeX
        imgSizeY = network.inputSizeY

        if sum(dataSetsRatios) != 1.0 or (0 > len(dataSetsRatios) > 3):
            raise HttpResponseBadRequest

        detaSetObjectsPks = {
            colorObject.nazwa:  self.divideImagesIntoSets(sessionId, imgSizeY, imgSizeX, dataSetsRatios, colorObject)
            for colorObject in Kolor.objects.all()
        }

        return JsonResponse({"dataSetIds": detaSetObjectsPks})

    def divideImagesIntoSets(self, sessionId, imgSizeY, imgSizeX, dataSetsRatios, colorObject):
        try:
            allImagesObjects = ObrazPoDostosowaniu.objects.filter(
                klatkaMacierzysta__film__sesja_id=sessionId,
                zlecenie__oczekiwanyRozmiarY=imgSizeY,
                zlecenie__oczekiwanyRozmiarX=imgSizeX,
                kolor=colorObject,
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
class Learn(View): #TODO: sprawdzic
    def post(self, request, **kwargs):
        data = json.loads(request.read().decode('utf-8').replace("'", "\""))

        description = data["describtion"] if "describtion" in data else None

        try:
            parametersId = data["parametersId"]
            dataSetIdsDict = data["dataSetIds"]
        except:
            raise HttpResponseBadRequest

        learnObjectPks = {
            color: self.addLearnObject(description, parametersId, dataSetId)
            for color, dataSetId in dataSetIdsDict.items()
        }

        return JsonResponse({"learnObjectPks": learnObjectPks})

    def get(self, request, **kwargs):
        try:
            learnObject = Uczenie.objects.filter(statusNauki='N')[0]
            color = learnObject.zbiory.kolor.nazwa if learnObject.zbiory and learnObject.zbiory.kolor else ""
            parameters = self.parametersToDict(learnObject, color)
            responseData = {
                "trainSet": self.setData(learnObject.zbiory.uczacy),
                "validatorSet": self.setData(learnObject.zbiory.walidacyjny),
                "testSet": self.setData(learnObject.zbiory.testowy),
                "parameters": parameters,
                "learn_id": learnObject.pk,
                "color": learnObject.zbiory.kolor.nazwa if learnObject.zbiory and learnObject.zbiory.kolor else ""
            }
            learnObject.statusNauki = 'T'
        except:
            raise Http404
        return JsonResponse(responseData)

    def addLearnObject(self, description, parametersId, dataSetId):
        learnObject = Uczenie.objects.create(opis=description, parametry_id=parametersId, zbiory_id=dataSetId)
        return learnObject.pk

    def setData(self, set):
        setPathsWithPositions = [
            [imgObject.getPath(), imgObject.pozycja.filter(status__status="punktOrginalny")[0]]
            for imgObject in set.iterator()
        ]
        setPathsWithPositions = [[patch, [position.x, position.y]] for patch, position in setPathsWithPositions]
        return setPathsWithPositions

    def parametersToDict(self, learnObject, color):
        parameters = learnObject.parametry
        pathToCreate = Path(os.path.join(parameters.zbiory.sesja.folderModele.getPath(), "model_{}".format(learnObject.pk)))
        pathToCreate.mkdir(parents=True, exist_ok=True)

        modelFile = os.path.join(
            parameters.zbiory.sesja.folderModele.getPath(),
            "model_{}_{}".format(learnObject.pk, color)
        )

        return { # nie zmieniac kluczy gdyz uzywane później(learnResponse) jako **kwargs dla funkcji
            "learning_rate": parameters.learning_rate,
            "batch_size": parameters.batch_size,
            "dropout": parameters.dropout,
            "training_iters": parameters.iloscIteracji,
            "epoch_size": parameters.epochSize,
            "save_step": parameters.saveStep,
            "network": json.loads(parameters.modelSieci.opisXML),
            "img_size_x": parameters.modelSieci.inputSizeX,
            "img_size_y": parameters.modelSieci.inputSizeY,
            "model_file": modelFile,
            "others": json.loads(parameters.opisUczeniaXML),
        }


@method_decorator(csrf_exempt, name='dispatch')
class LearnResults(JsonView):
    def post_method(self):
        data = self._data
        learn_result = WynikUczenia.objects.create(**data["result"])

        learn_object = Uczenie.objects.get(pk=data["learn_id"])
        learn_object.wynik=learn_result
        learn_object.statusNauki='K'
        learn_object.save()

        return JsonResponse({"ok": True})

    def get_method(self):
        pass
