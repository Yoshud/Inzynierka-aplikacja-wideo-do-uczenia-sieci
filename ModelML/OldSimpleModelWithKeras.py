import cv2
from pathlib import Path

from SplitMovieAppTracingModel import SplitMovieAppTracingModel
from typing import List, Dict, Tuple
from math import ceil

from dataBatchKeras import DataPicker
from simpleModelKeras import Model
from lossMethod import lossMethodDict, Norm2Loss
from optimizerMethod import optimizeMethodDict

import json
import shutil
import numpy as np

from copy import deepcopy

import sys

log = open("log.txt", "w")
sys.stderr = log
sys.stdout = log


class OldSimpleModelWithKeras(SplitMovieAppTracingModel):
    def __init__(self, network: str = None, others: str = None, tags: List[str] = None,
                 img_size_x: int = None,
                 img_size_y: int = None,
                 learning_rate: float = None,
                 batch_size: int = None,
                 dropout: float = None,
                 training_iters: int = None,
                 epoch_size: int = None,
                 save_step: int = None,
                 channels=3,
                 is_loading: bool = False,
                 models: List[Model] = None,
                 mean_and_std: List[Tuple[np.array, np.array]] = [],
                 input_size: Tuple[int, int] = None):

        if is_loading:
            super().__init__(tags=tags)
            self.input_size = input_size
            self.models = models
            self.mean_and_std = mean_and_std
        else:
            super().__init__(network, others, tags)
            self.input_size = (img_size_x, img_size_y)

            self.batch_size = batch_size
            self.training_iters = training_iters
            self.epoch_size = epoch_size
            self.save_step = save_step
            network = json.loads(network)
            others = json.loads(others)

            def objectParameters(others, object):
                object_parameters = others[object]
                object_type = object_parameters["type"]
                try:
                    object_params = object_parameters["parameters"]
                except KeyError:
                    object_params = {}
                return object_type, object_params

            def getLoss(others):
                loss_type, loss_params = objectParameters(others, "loss")
                loss_method = lossMethodDict[loss_type]
                if loss_params:
                    loss_method.set(**loss_params)
                return loss_method.get

            def getOptimizer(others, learning_rate):
                optimizerType, optimizerParams = objectParameters(others, "optimizer")
                optimizerParams["learning_rate"] = learning_rate

                optimizer = optimizeMethodDict[optimizerType].get(**optimizerParams)
                return optimizer

            self.models = []
            self.mean_and_std = []
            for i in range(len(tags)):
                model_network = deepcopy(network)
                model = Model(dropout, img_size_x, img_size_y, channels)
                model.add_conv_layers(model_network['conv_networks_dicts'])
                model.add_classifier("FC", {"full_connected_network_dicts": model_network['full_connected_network_dicts']})
                model.compile(
                    loss=getLoss(others),
                    optimizer=getOptimizer(others, learning_rate),
                    metrics=['mse', Norm2Loss().get],
                )

                self.models.append(model)
                self.mean_and_std.append((None, None))

    def save(self, path: Path):
        jsonFilePath = path / "index.json"
        index = {
            "input_size": self.input_size,
            "models": {}
        }
        for tag, model, mean_and_std in zip(self.tags, self.models, self.mean_and_std):
            path_to_create = path / tag
            if path_to_create.is_dir():
                shutil.rmtree(str(path_to_create))
            path_to_create.mkdir(parents=True, exist_ok=True)
            index["models"][tag] = str(path_to_create)

            model_file_path = str(path_to_create / "model")
            model.save(model_file_path)

            mean, std = mean_and_std
            np.save(path.joinpath(path_to_create, "mean.npy"), mean)
            np.save(path.joinpath(path_to_create, "std.npy"), std)

        with open(str(jsonFilePath), "w+") as jsonFile:
            jsonFile.write(json.dumps(index))

        shutil.copyfile("log.txt", str(path / "log.txt"))
        shutil.copyfile("response.json", str(path / "parameters.json"))

    @classmethod
    def load(cls, path: Path) -> "OldSimpleModelWithKeras":
        json_file_path = path / "index.json"
        json_file = open(str(json_file_path), 'r')
        index = json.loads(json_file.read())
        json_file.close()
        models_dict = index["models"]
        input_size = index["input_size"]
        tags = list(models_dict.keys())
        models = [Model.load(modelPath) for modelPath in models_dict.values()]

        mean_and_std = [(np.load(path.joinpath(modelPath, "mean.npy")), (np.load(path.joinpath(modelPath, "std.npy"))))
                        for modelPath in models_dict.values()]
        return OldSimpleModelWithKeras(
            is_loading=True,
            models=models,
            tags=tags,
            input_size=input_size,
            mean_and_std=mean_and_std
        )

    def predict(self, image: np.array) -> Dict[str, Tuple[float]]:
        image = self._prepare_image(image, self.input_size)
        only_one_images = np.array([image])
        return {tag: list(model.model.predict(only_one_images)) for tag, model in zip(self.tags, self.models)}

    def predict_batch(self, images: List[np.array]) -> List[Dict[str, Tuple[float]]]:
        images = [self._prepare_image(image, self.input_size) for image in images]
        return [self.predict(image) for image in images]

    def fit(self, train_data: List[dict], test_data: List[dict], validation_data: List[dict], *args, **kwargs):
        for tag, model, i in zip(self.tags, self.models, range(len(self.models))):
            model_train_data = [(el["path"], el["positions"][tag]) for el in train_data if el["positions"][tag] is not None]
            model_test_data = [(el["path"], el["positions"][tag]) for el in test_data if el["positions"][tag] is not None]
            model_validation_data = [(el["path"], el["positions"][tag]) for el in validation_data if el["positions"][tag] is not None]
            data_picker = DataPicker(
                self.batch_size, self.epoch_size, self.training_iters,
                model_train_data, model_test_data, model_validation_data,
                transform=lambda img: self._prepare_image(img, self.input_size)
            )

            number_of_epoch = max(1, ceil(self.training_iters / self.epoch_size))

            for epoch in range(number_of_epoch):
                if not epoch % 3:  # epoch per 1 data load
                    X, Y = data_picker.load_data()
                    validation = data_picker.load_validation_data()

                model.fit(
                    X, Y,
                    batch_size=self.batch_size,
                    validation_data=validation,
                    epochs=epoch + 1,
                    initial_epoch=epoch,
                )

            self.mean_and_std[i] = (data_picker.mean, data_picker.std)

    @classmethod
    def _prepare_image(cls, img, input_size):  # add standarization with value from model
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
#12600