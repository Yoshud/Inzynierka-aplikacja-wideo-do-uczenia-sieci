from keras.models import Sequential, model_from_json
from keras.layers import Dense, Conv2D, Flatten, Dropout, MaxPooling2D
from dataBatchKeras import Data_picker
from math import ceil, floor
from keras.utils import plot_model

from lossMethod import Norm2Loss


class Model:
    def __init__(self, dropout: float = None, img_size_x: int = None, img_size_y: int = None, channels: int = 3,
                 model=None):
        if model:
            self.model = model
            print("only load model - it can be only evaluate or save nothing more")
        else:
            self.model = Sequential()
            self.dropout = dropout
            self.input_shape = [img_size_x, img_size_y, channels]

            self.classifiers = {
                "FC": self._add_fc_classifier
            }

    def add_classifier(self, classifier_type="FC", classifier_kwargs: dict=dict()):
        self.classifiers[classifier_type](**classifier_kwargs)

    def add_conv_layers(self, conv_network_dicts: list):
        self._add_conv_layer(input_shape=self.input_shape, conv_network_dict=conv_network_dicts[0])

        for conv_network_dict in conv_network_dicts[1:]:
            self._add_conv_layer(conv_network_dict=conv_network_dict)

        self.model.add(Flatten())

        return self.model

    def compile(self, *args, **kwargs):
        return self.model.compile(*args, **kwargs)

    def fit(self, *args, **kwargs):
        return self.model.fit(*args, **kwargs)

    def save(self, fileName, epoch=None):
        if epoch:
            fileName = f"{fileName}_epoch{epoch}"

        model_json = self.model.to_json()
        with open(f"{fileName}.json", "w") as json_file:
            json_file.write(model_json)
        self.model.save_weights(f"{fileName}.h5")

    @classmethod
    def load(cls, fileName):
        json_file_name = f"{fileName}/model.json"
        model_file_name = f"{fileName}/model.h5"

        json_file = open(json_file_name, 'r')
        loaded_model_json = json_file.read()
        json_file.close()

        loaded_model = model_from_json(loaded_model_json)
        loaded_model.load_weights(model_file_name)

        return Model(model=loaded_model)

    def _add_conv_layer(self, conv_network_dict: dict, max_pool: int = None, input_shape: list = None):
        if 'window' in conv_network_dict:
            if 'kernel_size' not in conv_network_dict:
                conv_network_dict['kernel_size'] = conv_network_dict.pop('window')
            else:
                raise AttributeError

        if max_pool is None or 'max_pool' in conv_network_dict:
            max_pool = conv_network_dict.pop('max_pool')
        else:
            raise AttributeError

        layer_args = dict(
            padding='same',
            activation='relu',
            **conv_network_dict,
        )
        if input_shape:
            layer_args['input_shape'] = input_shape

        self.model.add(Conv2D(**layer_args))
        self.model.add(MaxPooling2D([max_pool, max_pool], padding='same')) if max_pool > 1 else None
        self.model.add(Dropout(self.dropout))

    def _add_fc_layer(self, full_connected_network_dict: dict):
        layer_args = dict(**full_connected_network_dict)
        if 'size' in layer_args:
            if 'units' not in layer_args:
                layer_args['units'] = layer_args.pop('size')
            else:
                raise AttributeError

        if 'relu' in layer_args:
            if layer_args['relu']:
                layer_args['activation'] = 'relu'

            layer_args.pop('relu')

        using_dropout = False
        if 'dropout' in layer_args and layer_args.pop('dropout'):
            using_dropout = True

        self.model.add(Dense(**layer_args))
        self.model.add(Dropout(self.dropout)) if using_dropout else None

        return self.model

    def _add_fc_classifier(self, full_connected_network_dicts: list):
        for full_connected_network_dict in full_connected_network_dicts:
            self._add_fc_layer(full_connected_network_dict)

        return self.model


def test(model:Model, batch_size: int, data_picker: Data_picker, **kwargs):
    is_loaded = True
    results = list()

    while is_loaded:
        X, Y, is_loaded = data_picker.load_test_data()
        results.extend(model.model.evaluate(X, Y, batch_size=batch_size))

    results
    return results


def train(training_iters, save_step, epoch_size, img_size_x, img_size_y, dropout, conv_networks_dicts, batch_size,
          full_connected_network_dicts, optimizer_type, loss_fun, data_picker: Data_picker, model_file: str,
          epoch_per_one_data_laod: int = 2, channels=3, **kwargs):
    model = Model(dropout, img_size_x, img_size_y, channels)

    model.add_conv_layers(conv_networks_dicts)
    model.add_classifier("FC", {"full_connected_network_dicts": full_connected_network_dicts})
    model.compile(
        loss=loss_fun,
        optimizer=optimizer_type,
        metrics=['mse', Norm2Loss().get],
    )

    plot_model(model, to_file=f'{model_file}.png')

    number_of_epoch = max(1, ceil(training_iters / epoch_size))
    epochs_to_save = max(1, floor(save_step / epoch_size))

    for epoch in range(number_of_epoch):
        if not epoch % epoch_per_one_data_laod:
            X, Y = data_picker.load_data()
            validation_data = data_picker.load_validation_data()

        train_history = model.fit(
            X, Y,
            batch_size=batch_size,
            validation_data=validation_data,
            epochs=epoch+1,
            initial_epoch=epoch,
        )

        if not epoch % epochs_to_save:
            model.save(model_file, epoch)
        train_history

    model.save(model_file)

    ##TODO: add testing model
