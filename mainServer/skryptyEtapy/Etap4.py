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
class DivideIntoSets(View): #TODO: zmodyfikowac do korzystania z nowej logiki
    def post(self, request, **kwargs):
        data = json.loads(request.read().decode('utf-8').replace("'", "\""))
        try:
            dataSetsRatios = data["dataSetRatios"]
            sessionId = data["sessionId"]
        except:
            raise HttpResponseBadRequest

        if sum(dataSetsRatios) != 1.0 or (0 > len(dataSetsRatios) > 3):
            raise HttpResponseBadRequest

        dataSetObjectPk = self.divideImagesIntoSets(sessionId, dataSetsRatios)

        return JsonResponse({"dataSetId": dataSetObjectPk})

    def divideImagesIntoSets(self, sessionId, dataSetsRatios):
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
class Learn(View):
    def post(self, request, **kwargs):
        data = json.loads(request.read().decode('utf-8').replace("'", "\""))

        description = data["describtion"] if "describtion" in data else None

        try:
            parametersId = data["parametersId"]
            dataSetId = data["dataSetId"]
        except:
            raise HttpResponseBadRequest

        return JsonResponse({"learnObjectId": self.addLearnObject(description, parametersId, dataSetId)})

    def get(self, request, **kwargs):
        try:
            learnObject = Uczenie.objects.filter(statusNauki='N')[0]
            parameters = self.parametersToDict(learnObject)
            #TODO: debug to have all points specified
            responseData = {
                "trainSet": self.setData(ObrazPoDostosowaniu.objects.filter(zbioryUczacy=learnObject.zbiory)),
                "validatorSet": self.setData(ObrazPoDostosowaniu.objects.filter(zbioryWalidacyjny=learnObject.zbiory)),
                "testSet": self.setData(ObrazPoDostosowaniu.objects.filter(zbioryTestowy=learnObject.zbiory)),
                "parameters": parameters,
                "learn_id": learnObject.pk,
            }
            learnObject.statusNauki = 'T'
        except:
            raise Http404

        return JsonResponse(responseData)

    def addLearnObject(self, description, parametersId, dataSetId):
        learnObject = Uczenie.objects.create(opis=description, parametry_id=parametersId, zbiory_id=dataSetId)
        return learnObject.pk

    def setData(self, set): # TODO: ogarnać
        setPathsWithPositionsJson = []
        for imgObject in set.iterator():
            path = imgObject.getPath()
            positions = json.loads(imgObject.pozycja.json.replace("'", "\"").replace("None", "null"))
            # positions = json.loads(imgObject.pozycja.json) #TODO: only because of fixed bug in stage3, remove in future!

            setPathsWithPositionsJson.append({"path": path, "positions": positions})

        return setPathsWithPositionsJson

    @staticmethod
    def getParameter(parameters: ParametryUczenia, key: str):
        if key in parameters.__dict__:
            return parameters.__getattribute__(key)
        else:
            return None

    def parametersToDict(self, learnObject): #TODO: inaczej rozwiązać zapisywanie modelu
        parameters = learnObject.parametry
        pathToCreate = Path(os.path.join(learnObject.zbiory.sesja.folderModele.getPath(), "model_{}".format(learnObject.pk)))
        pathToCreate.mkdir(parents=True, exist_ok=True)

        modelFile = os.path.join(
            pathToCreate,
            "model_{}".format(id(learnObject))
        )
        return { # nie zmieniac kluczy gdyz uzywane później(learnResponse) jako **kwargs dla funkcji
            "learning_rate": self.getParameter(parameters, "learning_rate"),
            "batch_size": self.getParameter(parameters, "batch_size"),
            "dropout": self.getParameter(parameters, "dropout"),
            "training_iters": self.getParameter(parameters, "iloscIteracji"),
            "epoch_size": self.getParameter(parameters, "epochSize"),
            "save_step": self.getParameter(parameters, "saveStep"),
            "network": self.getParameter(parameters.modelSieci, "opisJSON"),
            "img_size_x": self.getParameter(parameters.modelSieci, "inputSizeX"),
            "img_size_y": self.getParameter(parameters.modelSieci, "inputSizeY"),
            "model_file": modelFile,
            "others": self.getParameter(parameters, "opisUczeniaJSON"),
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
