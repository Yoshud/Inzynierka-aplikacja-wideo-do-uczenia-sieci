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
class DivideIntoSets(View):
    def post(self, request, **kwargs):
        data = json.loads(request.read().decode('utf-8').replace("'", "\""))
        try:
            dataSetsRatios = data["dataSetRatios"]
            sessionId = data["sessionId"]
            if sum(dataSetsRatios) != 1.0 or (0 > len(dataSetsRatios) > 3):
                raise HttpResponseBadRequest
        except:
            raise HttpResponseBadRequest
        try:
            allImagesObjects = ObrazPoDostosowaniu.objects.filter(klatkaMacierzysta__film__sesja_id=sessionId)
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
        return JsonResponse({"dataSetId": dataSetObject.pk})


@method_decorator(csrf_exempt, name='dispatch')
class Learn(View):
    def post(self, request, **kwargs):
        data = json.loads(request.read().decode('utf-8').replace("'", "\""))
        try:
            description = data["description"]
        except KeyError:
            description = None
        try:
            parametersId = data["parametersId"]
        except:
            raise HttpResponseBadRequest
        learnObject = Uczenie.objects.create(opis=description, parametry_id=parametersId)
        return JsonResponse({"learnId": learnObject.pk})

    def get(self, request, **kwargs):
        try:
            learnObject = Uczenie.objects.filter(statusNauki='N')[0]
            parameters = self.parametersToDict(learnObject)
            responseData = {
                "trainSet": self.setData(learnObject.parametry.zbiory.uczacy),
                "validatorSet": self.setData(learnObject.parametry.zbiory.walidacyjny),
                "testSet": self.setData(learnObject.parametry.zbiory.testowy),
                "parameters": parameters,
                "learn_id": learnObject.pk,
            }
            learnObject.statusNauki = 'T'
        except:
            raise Http404
        return JsonResponse(responseData)

    def setData(self, set):
        setPathsWithPositions = [
            [imgObject.sciezka, imgObject.pozycja.filter(status__status="punktOrginalny")[0]]
            for imgObject in set.iterator()
        ]
        setPathsWithPositions = [[patch, [position.x, position.y]] for patch, position in setPathsWithPositions]
        return setPathsWithPositions

    def parametersToDict(self, learnObject):
        parameters = learnObject.parametry
        pathToCreate = Path(os.path.join(parameters.zbiory.sesja.folderModele.sciezka, "model_{}".format(learnObject.pk)))
        pathToCreate.mkdir(parents=True, exist_ok=True)

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
            "model_file": os.path.join(parameters.zbiory.sesja.folderModele.sciezka, "model_{}".format(learnObject.pk)),
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
