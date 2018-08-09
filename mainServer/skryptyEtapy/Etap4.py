from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import Http404, HttpResponseServerError, HttpResponseBadRequest
from mainServer.skryptyEtapy.helpersMethod import *
import json
import os
from functools import reduce
from time import sleep
import numpy as np

@method_decorator(csrf_exempt, name='dispatch')
class DiviceIntoSets(View):
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
