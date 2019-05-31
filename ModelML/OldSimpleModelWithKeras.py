from pathlib import Path

from ModelML.SplitMovieAppTracingModel import SplitMovieAppTracingModel
from typing import List, Dict, Tuple, Optional
from ModelML.simpleModelKeras import Model
from ModelML.lossMethod import lossMethodDict, Norm2Loss
from ModelML.optimizerMethod import optimizeMethodDict

import json
import shutil


class OldSimpleModelWithKeras(SplitMovieAppTracingModel):
    pass

    #  x  fit tworzy datapickery z danych (albo napisze wlasny kerasowy tym razem)
    #  \/ __init__ z danych tworzy model i daje odpowiednie ustawienia resize
    #  \/  save - tworzy różne pliki i index.json (zawiera tez wielkosc wejscia) i tam zapisuje modele
    #  * load - czyta index.json i wczytuje modele
    #  x  predict - robi resize (i crop?) i używa wszystkich modeli i zwraca wyniki jako słownik
    def __init__(self, network: str, others: str, tags: List[str], #TODO: dodac opcje z JSONa (funkcja load)
                 img_size_x: int,
                 img_size_y: int,
                 learning_rate: float,
                 # batch_size: int,
                 dropout: float,
                 # training_iters: int,
                 # epoch_size: int,
                 # save_step: int,
                 # model_file: int, #TODO: zapisac te nieuzywane i uzyc ich w fit
                 channels=3):

        super().__init__(network, others, tags)
        self.input_size = (img_size_x, img_size_y)

        network = json.loads(network)
        others = json.loads(others)

        def objectParameters(others, object):
            objectParameters = others[object]
            objectType = objectParameters["type"]
            try:
                objectParams = objectParameters["parameters"]
            except KeyError:
                objectParams = {}
            return objectType, objectParams

        def getLoss(others):
            lossType, lossParams = objectParameters(others, "loss")
            lossMethod = lossMethodDict[lossType]
            if lossParams:
                lossMethod.set(**lossParams)
            return lossMethod.get

        def getOptimizer(others, learning_rate):
            optimizerType, optimizerParams = objectParameters(others, "optimizer")
            optimizerParams["learning_rate"] = learning_rate

            optimizer = optimizeMethodDict[optimizerType].get(**optimizerParams)
            return optimizer

        self.models = []
        for i in range(len(tags)):
            model = Model(dropout, img_size_x, img_size_y, channels)
            model.add_conv_layers(network['conv_networks_dicts'])
            model.add_classifier("FC", {"full_connected_network_dicts": network['full_connected_network_dicts']})
            model.compile(
                loss=getLoss(others),
                optimizer=getOptimizer(others, learning_rate),
                metrics=['mse', Norm2Loss().get],
            )

            self.models.append(model)

    def save(self, path: Path):
        for tag in self.tags:
            # create dirs with tagnames, add this dirs to JSON, add input_size to JSON,
            # save model in every dir (structure + weights)
            jsonFilePath = path / "index.json"
            index = {
                "input_size": self.input_size,
                "models": {}
            }
            for i, tag in enumerate(self.tags):
                pathToCreate = path / tag
                if pathToCreate.is_dir():
                    shutil.rmtree(str(pathToCreate))
                pathToCreate.mkdir(parents=True, exist_ok=True)
                index["models"][tag] = str(pathToCreate)

                modelFilePath = str(pathToCreate / "model")

                self.models[i].save(modelFilePath)

            with open(str(jsonFilePath)) as jsonFile:
                jsonFile.write(json.dumps(index))


    @classmethod
    def load(cls, path: Path) -> "OldSimpleModelWithKeras":
        jsonFilePath = path / "index.json"
        json_file = open(str(jsonFilePath), 'r')
        index = json.loads(json_file.read())
        json_file.close()
        #TODO: dodać rzeczy do init i wczytywac tutaj modele a potem je wrzucic w init bezposrednio
