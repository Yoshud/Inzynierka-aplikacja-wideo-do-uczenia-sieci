import tensorflow as tf
from abc import ABC, abstractmethod
import numpy as np
from ModelML.parameter import Parameter


class LossMethod(ABC):
    parameters: list = []

    @staticmethod
    def check_params(self, **params):
        return not np.in1d(self.parameters, params.keys())

    def set(self, **params):
        self.__dict__.update(params)

    @abstractmethod
    def get(self, pred, y):
        pass


class CombinedLoss(LossMethod):
    norm_2_ratio = 0.2
    subtract_ratio = 1.1
    parameters = [
        Parameter("norm_2_ratio", "float", 0.0, 5.0, 0.2).dict(),
        Parameter("subtract_ratio", "float", 0.0, 10.0, 1.1).dict(),
    ]

    def get(self, pred, y):
        return self.norm_2_ratio * tf.reduce_mean(
            tf.sqrt(tf.reduce_sum(tf.square(pred - y), 1))) + self.subtract_ratio * tf.reduce_mean(tf.abs(pred - y))


class Norm2Loss(LossMethod):
    def get(self, pred, y):
        return tf.reduce_mean(tf.sqrt(tf.reduce_sum(tf.square(pred - y), 1)))


class Norm2SimplerLoss(LossMethod):
    def get(self, pred, y):
        return tf.reduce_mean(tf.reduce_sum(tf.square(pred - y), 1))


class SquaredSubtract(LossMethod):
    def get(self, pred, y):
        return tf.reduce_mean(tf.square(pred - y))


lossMethodDict = {
    "combined": CombinedLoss(),
    "norm_2": Norm2Loss(),
    "norm_2_simpler": Norm2SimplerLoss(),
    "squared_subtract": SquaredSubtract(),
}
