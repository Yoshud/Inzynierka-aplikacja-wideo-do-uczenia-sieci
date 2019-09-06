from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View

from typing import List
import json

from lossMethods import lossMethodDict
from mainServer.stages.JsonView import JsonView
from mainServer.stages.auxiliaryMethods import *
from optimizerMethods import optimizeMethodDict


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
            "description": network.opisJSON
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
class Learn(JsonView):
    def post_method(self):
        description = self.get_data('description')
        parametersId = self.get_data_or_error('parametersId')
        dataSetId = self.get_data_or_error('dataSetId')

        return JsonResponse({"learnObjectId": self._addLearnObject(description, parametersId, dataSetId)})

    def get_method(self):
        try:
            learnObject = Uczenie.objects.filter(statusNauki='N')[0]
            sessionObject = learnObject.zbiory.sesja

            parameters = self._parametersToDict(learnObject, sessionObject)
            model_path = self._createModelPath(learnObject)
            sets = self._setsData(learnObject, sessionObject)

            responseData = {
                "sets": sets,
                "parameters": parameters,
                "learn_id": learnObject.pk,
                "model_path": model_path
            }
            learnObject.statusNauki = 'T'
        except:
            raise Http404

        return JsonResponse(responseData)

    @staticmethod
    def _addLearnObject(description, parametersId, dataSetId):
        learnObject = Uczenie.objects.create(opis=description, parametry_id=parametersId, zbiory_id=dataSetId)
        return learnObject.pk

    @classmethod
    def _createModelPath(cls, learnObject):
        modelPath = Path(
            os.path.join(learnObject.zbiory.sesja.folderModele.getPath(), "model_{}".format(learnObject.pk)))
        modelPath.mkdir(parents=True, exist_ok=True)
        return str(modelPath)

    @classmethod
    def _setData(cls, color_set, sessionObject):
        setPathsWithPositionsJson = []
        for imgObject in color_set.iterator():
            path = imgObject.getPath()
            positions = json.loads(imgObject.pozycja.json.replace("'", "\"").replace("None", "null"))
            # positions = json.loads(imgObject.pozycja.json) TODO:only because of fixed bug in stage3, remove in future!

            # TODO: Do something to ensure we have all points specified (its just walk around)
            positions = cls.fillPositionSet(positions, sessionObject)
            setPathsWithPositionsJson.append({"path": path, "positions": positions})

        return setPathsWithPositionsJson

    @classmethod
    def _setsData(cls, learnObject, sessionObject):
        setsData = {
            "train_data": cls._setData(ObrazPoDostosowaniu.objects.filter(zbioryUczacy=learnObject.zbiory),
                                       sessionObject),

            "validation_data": cls._setData(ObrazPoDostosowaniu.objects.filter(zbioryWalidacyjny=learnObject.zbiory),
                                            sessionObject),

            "test_data": cls._setData(ObrazPoDostosowaniu.objects.filter(zbioryTestowy=learnObject.zbiory),
                                      sessionObject),
        }
        return setsData

    @classmethod
    def fillPositionSet(cls, positions: dict, sessionObject: Sesja):
        for color in cls.sessionColorsTags(sessionObject):
            if color not in positions:
                positions[color] = None
        return positions

    @staticmethod
    def getParameter(parameters: ParametryUczenia, key: str):
        if key in parameters.__dict__:
            return parameters.__getattribute__(key)
        else:
            return None

    @staticmethod
    def sessionColorsTags(sessionObject: Sesja) -> List[str]:
        return [colorObject.nazwa for colorObject in sessionObject.zbiorKolorow.kolory.iterator()]

    @classmethod
    def _parametersToDict(cls, learnObject, sessionObject):
        parameters = learnObject.parametry

        return {  # nie zmieniac kluczy gdyz uzywane później(learnResponse) jako **kwargs dla funkcji
            "learning_rate": cls.getParameter(parameters, "learning_rate"),
            "batch_size": cls.getParameter(parameters, "batch_size"),
            "dropout": cls.getParameter(parameters, "dropout"),
            "training_iters": cls.getParameter(parameters, "iloscIteracji"),
            "epoch_size": cls.getParameter(parameters, "epochSize"),
            "save_step": cls.getParameter(parameters, "saveStep"),
            "network": cls.getParameter(parameters.modelSieci, "opisJSON"),
            "img_size_x": cls.getParameter(parameters.modelSieci, "inputSizeX"),
            "img_size_y": cls.getParameter(parameters.modelSieci, "inputSizeY"),
            "others": cls.getParameter(parameters, "opisUczeniaJSON"),
            "tags": cls.sessionColorsTags(sessionObject)
        }


@method_decorator(csrf_exempt, name='dispatch')
class LearnResults(JsonView):
    def post_method(self):
        data = self._data
        learn_result = WynikUczenia.objects.create(**data["result"])

        learn_object = Uczenie.objects.get(pk=data["learn_id"])
        learn_object.wynik = learn_result
        learn_object.statusNauki = 'K'
        learn_object.save()

        return JsonResponse({"ok": True})
