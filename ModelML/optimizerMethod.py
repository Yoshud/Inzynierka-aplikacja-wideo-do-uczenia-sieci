from tensorflow import train as tf
from tensorflow.python.training.optimizer import Optimizer
import numpy as np


class OptimizeMethod:
    def __init__(self, method, requirements: list, optional: list):
        self.requirements = requirements
        self.optional = optional
        # if not isinstance(method, Optimizer):
        #     raise TypeError
        self.method = method

    def get(self, **params):
        full_list = np.array(self.requirements + self.optional)
        if (not np.in1d(params.keys(), full_list)) or (not np.in1d(self.requirements, params.keys())):
            # raise
            pass
        return self.method(**params)


optimizeMethodDict = {
    "momentum": OptimizeMethod(
        method=tf.MomentumOptimizer,
        requirements=["momentum", ],
        optional=["use_nesterov", "use_locking"]
    ),
    "adam": OptimizeMethod(
        method=tf.AdamOptimizer,
        requirements=[],
        optional=["beta1", "beta2", "epsilon", "use_locking"]
    ),
    "ftrl": OptimizeMethod(
        method=tf.FtrlOptimizer,
        requirements=[],
        optional=[
            "learning_rate_power", "initial_accumulator_value", "l1""_regularization_strength",
            "l2""_regularization_strength", "use_locking", "name", "l2""_shrinkage_regularization_strength"
        ]
    ),
    "RMSProp": OptimizeMethod(
        method=tf.RMSPropOptimizer,
        requirements=[],
        optional=["decay", "momentum", "epsilon", "use_locking", "centered"]
    )
}
