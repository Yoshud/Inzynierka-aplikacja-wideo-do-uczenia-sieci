from keras.models import Sequential
from keras.layers import Dense, Conv2D, Flatten, Dropout, MaxPooling2D
from ModelML.dataBatchKeras import Data_picker
from math import ceil, floor
from keras.utils import plot_model
from keras.models import load_model

from ModelML.lossMethod import Norm2Loss


class Model:
    def __init__(self, dropout: float, img_size_x: int, img_size_y: int, channels: int = 3):
        self.model = Sequential()
        self.dropout = dropout
        self.input_shape = [img_size_x, img_size_y, channels]

        self.classifiers = {
            "FC": self._add_fc_classifier
        }

    def add_classifier(self, classifier_type="FC", classifier_kwargs: dict={}):
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

    def _add_conv_layer(self, conv_network_dict: dict, max_pool: int = 1, input_shape: list = None):
        layer_args = dict(
            filters=conv_network_dict["filters"],
            kernel_size=conv_network_dict["window"],
            padding='same',
            activation='relu',
            **conv_network_dict,
        )
        if input_shape:
            layer_args['input_shape'] = input_shape

        self.model.add(Conv2D(layer_args))
        self.model.add(MaxPooling2D([max_pool, max_pool], padding='same')) if max_pool > 1 else None
        self.model.add(Dropout(self.dropout))

    def _add_fc_layer(self, full_connected_network_dict: dict):
        layer_args = dict(units=full_connected_network_dict['size'], **full_connected_network_dict)

        if full_connected_network_dict['relu']:
            layer_args['activation'] = 'relu'

            self.model.add(Dense(**layer_args))
            self.model.add(Dropout(self.dropout)) if full_connected_network_dict['dropout'] else None

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

    return results


def train(training_iters, save_step, epoch_size, img_size_x, img_size_y, dropout, conv_networks_dicts, batch_size,
          full_connected_network_dicts, optimizer_type, loss_fun, data_picker: Data_picker, model_file: str, channels=3,
          **kwargs):
    model = Model(dropout, img_size_x, img_size_y, channels)

    model.add_conv_layers(conv_networks_dicts)
    model.add_classifier("FC", full_connected_network_dicts)

    model.compile(
        loss=loss_fun,
        optimizer=optimizer_type,
        metrics=['mse', Norm2Loss.get],
    )

    plot_model(model, to_file='model.png')

    number_of_epoch = max(1, ceil(training_iters / epoch_size))
    epochs_to_save = max(1, floor(save_step / epoch_size))

    for epoch in range(number_of_epoch):
        train_history = model.fit(
            *data_picker.load_data(),
            batch_size=batch_size,
            validation_data=data_picker.load_validation_data(),
            epochs=epoch+1,
            steps_per_epoch=epoch_size,
            initial_epoch=epoch,
            validation_step=10
        )
        if not epoch % epochs_to_save:
            model.model.save(f"{model_file}_epoch{epoch}.h5")

        model.model.save(f"{model_file}.h5")



    ##TODO: add testing model

    ##TODO: add postgres
