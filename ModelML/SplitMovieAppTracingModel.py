from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np
from abc import ABC, abstractmethod


# Base class to implement
class SplitMovieAppTracingModel(ABC):
    @abstractmethod
    def __init__(self, network: Optional[str], others: Optional[str], tags: Optional[List[str]],
                 img_size_x: Optional[int],
                 img_size_y: Optional[int],
                 learning_rate: Optional[float],
                 batch_size: Optional[int],
                 dropout: Optional[float],
                 training_iters: Optional[int],
                 epoch_size: Optional[int],
                 save_step: Optional[int]):
        """__init__ should be call only internally in split movie app, in all other cases Model shouldn't be construct
        but only loading from file by load classmethod"""

        self.tags = tags

    @abstractmethod
    def save(self, path: Path) -> bool:
        pass

    @classmethod
    @abstractmethod
    def load(cls, path: Path) -> "SplitMovieAppTracingModel":
        pass

    def fit(self, train_data: List[dict], test_data: List[dict], validation_data: List[dict], *args, **kwargs):
        """data should be list of dicts like:
        {
            "path": <path>
            "positions": Dict(<color_tag>, Tuple(<x>, <y>))
        }
        serializable as JSON
        suggest to use BGR image format like in cv2
        """
        pass

    @abstractmethod
    def predict(self, image: np.array) -> Dict[str, Tuple[float]]:
        """return should be dict:
        {
            <color_tag>: Tuple(<x>, <y>)
        }
        suggest to use BGR image format like in cv2 (but format should be in accordance with image format used in fit)
        """
        pass

    @abstractmethod
    def predict_batch(self, images: List[np.array]) -> List[Dict[str, Tuple[float]]]:
        """like predict but with batch of images"""
        pass
