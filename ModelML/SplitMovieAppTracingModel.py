from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np
from abc import ABC, abstractmethod


# Base class to implement
class SplitMovieAppTracingModel(ABC):
    @abstractmethod
    def __init__(self, network: Optional[str] = None, others: Optional[str] = None, tags: Optional[List[str]] = None,
                 img_size_x: Optional[int] = None,
                 img_size_y: Optional[int] = None,
                 learning_rate: Optional[float] = None,
                 batch_size: Optional[int] = None,
                 dropout: Optional[float] = None,
                 training_iters: Optional[int] = None,
                 epoch_size: Optional[int] = None,
                 save_step: Optional[int] = None):
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

    @abstractmethod
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
