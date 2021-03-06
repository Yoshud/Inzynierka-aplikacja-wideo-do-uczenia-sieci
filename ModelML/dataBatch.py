from typing import Callable, Optional

import numpy as np
import cv2


class GetNextBatch:
    def __init__(self, data, batch_size, full_random=True, start_point=0, randomize=True, without_loop=False):
        self._batch_size = batch_size
        self._full_random = full_random
        self._randomize = randomize
        data = np.array(data, dtype=object)

        if without_loop:
            self._data = data
            self._start_point = start_point
            self._method = self.get_normal
        else:
            if full_random:
                self._data = data
                self._method = self.get_random_batch
            else:
                self._data = np.random.permutation(data) if randomize else data
                self._start_point = start_point
                self._method = self.get_modulo

    def get_normal(self):
        end_point = (self._start_point + self._batch_size)
        data = self._data[self._start_point:end_point]
        self._start_point = end_point
        return data

    def get_modulo(self):
        data_len = len(self._data)
        end = (self._start_point + self._batch_size + 1) % data_len
        start = end - self._batch_size
        data = np.append(self._data[(data_len + start):data_len], self._data[max(0, start):end], axis=0)
        self._start_point = self._start_point + self._batch_size
        return data

    def get_random_batch(self):
        batch = np.random.permutation(self._data)[:int(self._batch_size)]
        return batch

    def get(self):
        return self._method()

    def data(self, data, start_point=0):
        if self._full_random:
            self._data = data
            self._method = self.get_random_batch
        else:
            self._data = np.random.permutation(data) if self._randomize else data
            self._start_point = start_point


class DataPicker:
    def __init__(self, batch_size, epoch_size, training_iters, train_patches_with_positions,
                 test_patches_with_positions=list(), validate_patches_with_positions=list(),
                 transform: Optional[Callable]=None, randomize=True,
                 max_size_of_draw=10000): #TODO: połączenie z epoch_size tak by była używana gdy jest mniejsza jak cała ilość danych
        self.transform = transform
        self._test_exist = len(test_patches_with_positions) > 0
        self._validation_exist = len(validate_patches_with_positions) > 0
        self.mean = None
        self.std = None

        size_of_batch = min(max_size_of_draw, int(batch_size * epoch_size), len(train_patches_with_positions))
        size_of_batch_test = min(max_size_of_draw, int(batch_size * epoch_size), len(test_patches_with_positions))
        size_of_batch_validation = min(
            max_size_of_draw, int(batch_size * epoch_size), len(validate_patches_with_positions)
        )

        if randomize:
            if batch_size * training_iters > 2 * len(train_patches_with_positions):
                self._load_method = GetNextBatch(train_patches_with_positions, size_of_batch, full_random=True).get
            else:
                self._load_method = \
                    GetNextBatch(train_patches_with_positions, size_of_batch, full_random=False).get
                
            if batch_size * training_iters > len(validate_patches_with_positions):
                self._validation_load_method = \
                    GetNextBatch(validate_patches_with_positions, size_of_batch_validation, full_random=True).get
            else:
                self._validation_load_method = \
                    GetNextBatch(validate_patches_with_positions, size_of_batch_validation, full_random=False).get
        
        else:
            self._load_method = \
                GetNextBatch(train_patches_with_positions, size_of_batch, full_random=False, randomize=False).get
            
            self._validation_load_method = \
                GetNextBatch(
                    validate_patches_with_positions, size_of_batch_validation, full_random=False, randomize=False
                ).get

        self._test_load_method = \
            GetNextBatch(test_patches_with_positions, size_of_batch_test, without_loop=True).get

    def load_test_data(self):
        if self._test_exist:
            data = self._test_load_method()
            X, Y = self._return_from_patches_with_positions(data)
            return X, Y, len(data) > 0

    def load_data(self):
        return self._return_from_patches_with_positions(self._load_method())

    def load_validation_data(self):
        if self._validation_exist:
            return self._return_from_patches_with_positions(self._validation_load_method())

    @staticmethod
    def standarize(data, mean=None, std=None):  # After first iteration remember standarized values and save them
        mean = data.mean(axis=0) if mean is None else mean
        std = data.std(axis=0) if std is None else std
        return (data - mean) / (std + 0.00001), mean, std

    def is_standarized(self):
        return self.mean is not None and self.std is not None

    def _return_from_patches_with_positions(self, patches_with_positions, standarize=True):
        X_1 = list()
        Y = np.zeros([len(patches_with_positions), 2])

        for i, (path, position) in enumerate(patches_with_positions):
            try:
                img = self.transform(cv2.imread(path)) if self.transform is not None else cv2.imread(path)
                X_1.append(img)
                Y[i, :] = position
            except:
                print(path)

        X = np.array(X_1)

        if standarize:
            standarized, self.mean, self.std = self.standarize(X, self.mean, self.std)
            return standarized, Y
        else:
            return X, Y
