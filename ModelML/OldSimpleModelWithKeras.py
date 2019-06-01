import cv2
from pathlib import Path

from ModelML.SplitMovieAppTracingModel import SplitMovieAppTracingModel
from typing import List, Dict, Tuple, Optional
from ModelML.simpleModelKeras import Model
from ModelML.lossMethod import lossMethodDict, Norm2Loss
from ModelML.optimizerMethod import optimizeMethodDict

import json
import shutil
import numpy as np


class OldSimpleModelWithKeras(SplitMovieAppTracingModel):
    pass

    #  x  fit tworzy datapickery z danych (albo napisze wlasny kerasowy tym razem)
    #  \/ __init__ z danych tworzy model i daje odpowiednie ustawienia resize
    #  \/  save - tworzy różne pliki i index.json (zawiera tez wielkosc wejscia) i tam zapisuje modele
    #  \/ load - czyta index.json i wczytuje modele
    #  x  predict - robi resize (i crop?) i używa wszystkich modeli i zwraca wyniki jako słownik

    # TODO: dodac opcje z JSONa (funkcja load)
    def __init__(self, network: str = None, others: str = None, tags: List[str] = None,
                 img_size_x: int = None,
                 img_size_y: int = None,
                 learning_rate: float = None,
                 batch_size: int = None,
                 dropout: float = None,
                 training_iters: int = None,
                 epoch_size: int = None,
                 save_step: int = None,
                 model_file: int = None,  # TODO: zapisac te nieuzywane i uzyc ich w fit
                 channels=3,
                 is_loading: bool = False,
                 models: List[Model] = None,
                 input_size: Tuple[int, int] = None):
        if is_loading:
            super().__init__(tags=tags)
            self.input_size = input_size
            self.models = models
        else:
            super().__init__(network, others, tags)
            self.input_size = (img_size_x, img_size_y)

            self.batch_size = batch_size
            self.training_iters = training_iters
            self.epoch_size = epoch_size
            self.save_step = save_step
            self.model_file = model_file
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

                self.models[i].save(modelFilePath)

            with open(str(jsonFilePath)) as jsonFile:
                jsonFile.write(json.dumps(index))

    @classmethod
    def load(cls, path: Path) -> "OldSimpleModelWithKeras":
        jsonFilePath = path / "index.json"
        json_file = open(str(jsonFilePath), 'r')
        index = json.loads(json_file.read())
        json_file.close()
        modelsDict = index["models"]
        input_size = index["input_size"]
        tags = list(modelsDict.keys())
        models = [Model.load(modelPath) for modelPath in modelsDict.values()]
        return OldSimpleModelWithKeras(is_loading=True, models=models, tags=tags, input_size=input_size)

    def predict(self, image: np.array) -> Dict[str, Tuple[float]]:
        pass

    @classmethod
    def _prepare_image(cls, img, input_size):
        img_height = img.shape[0]
        crop_position = cls._image_center(img.shape)

        crop = cls._crop(img, img_height, img_height, *crop_position)

        return cls._resize(crop, input_size)

    @classmethod
    def _crop(cls, img, height, width, x0=-1, y0=-1):
        x0 = img.shape[0] / 2 if x0 == -1 else x0
        y0 = img.shape[1] / 2 if y0 == -1 else y0

        xmin = int(x0 - height / 2)
        xmax = int(x0 + height / 2)
        ymin = int(y0 - width / 2)
        ymax = int(y0 + width / 2)

        return img[ymin:ymax, xmin:xmax]

    @classmethod
    def _image_center(cls, img_shape):
        img_size = np.array(img_shape[1::-1])
        img_center = img_size / 2
        return img_center

    @classmethod
    def _resize(cls, img, size=(0, 0), scale=0):
        img = cv2.resize(img, tuple(size), scale, scale, interpolation=cv2.INTER_AREA)
        return img
