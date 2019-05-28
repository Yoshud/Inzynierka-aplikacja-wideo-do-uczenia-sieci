from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np
from abc import ABC, abstractmethod


# Base class to implement
class SplitMovieAppTracingModel(ABC):
    @abstractmethod
    def __init__(self, network: str, others: str,
                 img_size_x: Optional[int],
                 img_size_y: Optional[int],
                 learning_rate: Optional[float],
                 batch_size: Optional[int],
                 dropout: Optional[float],
                 training_iters: Optional[int],
                 epoch_size: Optional[int],
                 save_step: Optional[int],
                 model_file: Optional[str]):
        pass
    """__init__ should be call only internally in split movie app, in all other cases Model shouldn't be construct 
    but only loading from file by load classmethod"""

    @abstractmethod
    def save(self, path: Path) -> bool:
        pass

    @classmethod
    @abstractmethod
    def load(cls, path: Path) -> "Model":
        pass

    def fit(self, data: List[dict], *args, **kwargs):
        """data should be list of dicts like:
        {
            "path": <path>
            "positions": Dict(<color_tag>, Tuple(<x>, <y>))
        }
        serializable as JSON
        """
        pass

    @abstractmethod
    def predict(self, image: np.array) -> Dict[str, Tuple[float]]:
        """return should be dict:
        {
            <color_tag>: Tuple(<x>, <y>)
        }
        """
        pass

    @abstractmethod
    def predict_batch(self, images: List[np.array]) -> List[Dict[str, Tuple[float]]]:
        """like predict but with batch of images"""
        pass
