import numpy as np
from scipy.misc import imread


class Get_next_batch:
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
                 max_size_of_draw=10000):
        self._img_size = img_size

        size_of_batch = min(max_size_of_draw, int(batch_size * epoch_size), len(train_patches_with_positions))
        size_of_batch_test = min(max_size_of_draw, int(batch_size * epoch_size), len(test_patches_with_positions))
        size_of_batch_validation = min(
            max_size_of_draw, int(batch_size * epoch_size), len(validate_patches_with_positions)
        )
        size_of_draw_tmp = int(batch_size * epoch_size / 4)
        size_of_draw = min(max_size_of_draw, size_of_draw_tmp, len(train_patches_with_positions))
        size_of_draw_validation = min(max_size_of_draw, size_of_draw_tmp, len(validate_patches_with_positions))
        
        k = 2 if len(validate_patches_with_positions) > size_of_batch/8 else 1 

        if randomize:
            if batch_size * training_iters > len(train_patches_with_positions):
                self._load_method = Get_next_batch(train_patches_with_positions, size_of_draw/k, full_random=True).get
            else:
                self._load_method = \
                    Get_next_batch(train_patches_with_positions, size_of_batch/k, full_random=False).get
                
            if batch_size * training_iters > len(validate_patches_with_positions):
                self._validation_load_method = \
                    Get_next_batch(validate_patches_with_positions, size_of_draw_validation/k, full_random=True).get
            else:
                self._validation_load_method = \
                    Get_next_batch(validate_patches_with_positions, size_of_batch_validation/k, full_random=False).get
        
        else:
            self._load_method = \
                Get_next_batch(train_patches_with_positions, size_of_batch/k, full_random=False, randomize=False).get
            
            self._validation_load_method = \
                Get_next_batch(
                    validate_patches_with_positions, size_of_batch_validation/k, full_random=False, randomize=False
                ).get

        self._test_load_method = \
            Get_next_batch(test_patches_with_positions, size_of_batch_test, without_loop=True).get

    def load_test_data(self):
        data = self._test_load_method()
        X, Y = self._return_from_patches_with_positions(data)
        return X, Y, len(data) > 0

    def load_data(self):
        return self._return_from_patches_with_positions(self._load_method())

    def load_validation_data(self):
        return self._return_from_patches_with_positions(self._validation_load_method())

    @staticmethod
    def _standarize(data):
        mean = data.mean(axis=0)
        std = data.std(axis=0)
        return (data - mean) / (std + 0.00001)

    def _return_from_patches_with_positions(self, patches_with_positions, standarize=True):
        imgN = self._img_size[0] * self._img_size[1] * 3
        X = np.zeros([len(patches_with_positions), imgN])
        Y = np.zeros([len(patches_with_positions), 2])

        for i, (path, position) in enumerate(patches_with_positions):
            try:
                img = imread(path)
                X[i, :] = img.flatten()
                Y[i, :] = position
            except:
                print(path)

        return (self._standarize(X), Y) if standarize else (X, Y)
