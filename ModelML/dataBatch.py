import numpy as np
import os
from scipy.misc import imread


class Get_next_batch:
    def __init__(self, data, batch_size, full_random, start_point=0, randomize=True):
        self._batch_size = batch_size
        self._full_random = full_random
        self._randomize = randomize
        data = np.array(data, dtype=object)
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
        batch = np.random.permutation(self._data)[:self._batch_size]
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


class Data_picker:
    def __init__(self, batch_size, epoch_size, training_iters, img_size, train_patches_with_positions,
                 test_patches_with_positions=list(), validate_patches_with_positions=list(), randomize=True,
                 max_size_of_draw=10000, loadData=False):
        self._batch_size = batch_size
        self._epoch_size = epoch_size
        self._training_iters = training_iters
        self._train_patches_with_positions = train_patches_with_positions
        self._randomize = randomize
        self._img_size = img_size

        self._number_of_draw = int(training_iters / epoch_size) + 1
        self._size_of_draw = int(batch_size * epoch_size * 2)  # poprawic
        self._size_of_draw = min(max_size_of_draw, self._size_of_draw, len(train_patches_with_positions))

        if randomize:
            if batch_size * training_iters > len(train_patches_with_positions):
                self._load_method = \
                    Get_next_batch(self._train_patches_with_positions, self._size_of_draw, full_random=True).get
                self._batch_functor = Get_next_batch([], batch_size, full_random=True)
            else:
                self._load_method = \
                    Get_next_batch(self._train_patches_with_positions, int(batch_size * epoch_size),
                                   full_random=False).get
                self._batch_functor = Get_next_batch([], batch_size, full_random=False)
        else:
            self._load_method = \
                Get_next_batch(self._train_patches_with_positions, int(batch_size * epoch_size), full_random=False,
                               randomize=False).get
            self._batch_functor = Get_next_batch([], batch_size, full_random=False, randomize=False)

        if loadData:
            self._data = self._load_method()

    def data_batch(self, iter):
        if not iter % self._epoch_size: #naprawic, bo prawdopodobnie zle dziala
            X, Y = self._return_from_patches_with_positions(self._load_method())
            self._data = list(zip(*(X, Y)))
            self._batch_functor.data(self._data)

        return zip(*self._batch_functor.get())

    def test_batch(self, iter):
        pass

    def _standarize(self, data):
        mean = data.mean(axis=0)
        std = data.std(axis=0)
        return (data - mean) / (std + 0.00001)

    def _return_from_patches_with_positions(self, patches_with_positions):
        imgN = self._img_size[0] * self._img_size[1] * 3
        X = np.zeros([len(patches_with_positions), imgN])
        Y = np.zeros([len(patches_with_positions), 2])

        for i, (patch, position) in enumerate(patches_with_positions):
            img = imread(patch)
            X[i, :] = img.flatten()
            Y[i, :] = position

        return X, Y

    def _load_method_template(self, load_method):
        return self._return_from_patches_with_positions(load_method())
