from tensorflow import train as tf
from tensorflow.python.training.optimizer import Optimizer
import numpy as np
from ModelML.parameter import Parameter


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
        requirements=[Parameter("momentum", "float", 0.0, 1.0, 0.9).dict(), ],
        optional=[
            Parameter("use_nesterov", "bool").dict(),
            Parameter("use_locking", "bool").dict()
        ]
    ),
    "adam": OptimizeMethod(
        method=tf.AdamOptimizer,
        requirements=[],
        optional=[
            Parameter("beta1", "float", 0.0, default=0.9).dict(),
            Parameter("epsilon", "float", 0.0, default=1e-8).dict(),
            Parameter("beta2", "float", 0.0, default=0.999).dict(),
            Parameter("use_locking", "bool").dict()
        ]
    ),
    "ftrl": OptimizeMethod(
        method=tf.FtrlOptimizer,
        requirements=[],
        optional=[
            Parameter("learning_rate_power", "float", -999, 0.0, 0.5).dict(),
            Parameter("initial_accumulator_value", "float", 0.0, 1.0, 0.1).dict(),
            Parameter("l1_regularization_strength", "float", 0.0, default=0.0).dict(),
            Parameter("l2_regularization_strength", "float", 0.0, default=0.0).dict(),
            Parameter("use_locking", "bool").dict(),
            Parameter("l2_shrinkage_regularization_strength", "float", 0.0, default=0.0).dict(),
        ]
    ),
    "RMSProp": OptimizeMethod(
        method=tf.RMSPropOptimizer,
        requirements=[],
        optional=[
            Parameter("decay", "float", 0.0, 1.0, 0.9).dict(),
            Parameter("momentum", "float", 0.0, 1.0, 0.0).dict(),
            Parameter("epsilon", "float", 0.0, 1.0, 1e-10).dict(),
            Parameter("use_locking", "bool").dict(),
            Parameter("centered", "bool").dict()
        ]
    )
}
