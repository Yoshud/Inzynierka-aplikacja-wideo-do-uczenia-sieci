import numpy as np
from dataBatch import Data_picker
from functools import reduce
import tensorflow as tf
import datetime as dt
import json
import sys

log = open("log.txt", "w")
sys.stderr = log
sys.stdout = log


def conv2d(img, w, b):
    return tf.nn.relu(
        tf.nn.bias_add(tf.nn.conv2d(img, w, strides=[1, 1, 1, 1], padding='SAME'), b))  # strides - przesuwanie okienka


def max_pool(img, k):
    return tf.nn.max_pool(img, ksize=[1, k, k, 1], strides=[1, k, k, 1], padding='SAME')


def conv_net(_X, _conv_network_variables_dicts, _fc_network_variables_dicts, _conv_out_size, _dropout, img_size_x,
             img_size_y, channels):
    _X = tf.reshape(_X, shape=[-1, img_size_x, img_size_y, channels])
    print(_X.shape, flush=True)

    def one_conv_layer(conv_before, conv_network_variables_dict):
        k = conv_network_variables_dict['max_pool']
        conv = conv2d(conv_before, conv_network_variables_dict['weights'], conv_network_variables_dict['biases'])
        conv = conv if k == 1 else max_pool(conv, k)
        return conv

    def one_fc_layer(layer_before, fc_network_variables_dict):
        weight = fc_network_variables_dict["weight"]
        bias = fc_network_variables_dict["bias"]
        relu = fc_network_variables_dict["relu"]
        dropout = fc_network_variables_dict["dropout"]
        dense = tf.add(tf.matmul(layer_before, weight), bias)
        if relu:
            dense = tf.nn.relu(dense)
        if dropout:
            tf.nn.dropout(dense, _dropout)
        return dense

    conv_out = reduce(one_conv_layer, _conv_network_variables_dicts, _X)
    transformed_conv_out = tf.reshape(conv_out, [-1, _conv_out_size])
    out = reduce(one_fc_layer, _fc_network_variables_dicts, transformed_conv_out)

    return out


def init_conv_variables(conv_networks_dicts, img_size_x, img_size_y, channels):
    n_input = img_size_x * img_size_y
    conv_network_variables_dicts = list()

    def append_weight_and_bias(filters_before, net_dict, conv_network_variables_dicts=conv_network_variables_dicts):
        window = net_dict['window']
        init_w = filters_before * np.prod(window) if filters_before > 0 else n_input
        bef_filters = filters_before if filters_before > 0 else 1
        init_w = np.sqrt(2.0 / init_w)

        conv_network_variables_dicts.append({
            'weights': tf.Variable(init_w * tf.random_normal([window[0], window[1], bef_filters, net_dict['filters']])),
            'biases': tf.Variable(0.1 * tf.random_normal([net_dict['filters']])),
            'max_pool': net_dict['max_pool'],
        })
        return net_dict['filters']

    reduce(append_weight_and_bias, conv_networks_dicts, channels)

    max_pool_dimension_reduce = np.prod([dict_el['max_pool'] for dict_el in conv_networks_dicts])
    max_pool_dimension_reduce = max_pool_dimension_reduce if max_pool_dimension_reduce > 0 else 1
    conv_out_size = \
        int(img_size_x / max_pool_dimension_reduce) * int(img_size_y / max_pool_dimension_reduce) * conv_networks_dicts[-1]['filters']

    return conv_network_variables_dicts, conv_out_size


def init_fc_variables(fc_network_dicts, conv_out_size):
    fc_network_variables_dicts = list()

    def append_weights_and_biases_for_fullconnected(inputSize, information,
                                                    fc_network_variables_dicts=fc_network_variables_dicts):
        init = np.sqrt(2.0 / inputSize)
        output_size = information["size"]
        weight = tf.Variable(init * tf.random_normal([inputSize, output_size]))
        bias = tf.Variable(0.1 * tf.random_normal([output_size]))
        fc_network_variables_dicts.append({  # "zwracana" wartosc (tamta jest zwracana ze wzgledu na reduce
            "weight": weight,
            "bias": bias,
            "relu": information["relu"],
            "dropout": information["dropout"]
        })
        return output_size

    reduce(append_weights_and_biases_for_fullconnected, fc_network_dicts, conv_out_size)

    return fc_network_variables_dicts


def test_model(sess: tf.Session, data_picker: Data_picker, pred, x, keep_prob): #zdefiniować pobieranie danych testowych
    errors = []
    test_batch_x, test_batch_y = data_picker.test_batch()
    while len(test_batch_x):
        it = 0
        for model_out, y_exp in zip(sess.run(pred, feed_dict={x: test_batch_x, keep_prob: 1.}), test_batch_y):
            error = np.mean(np.sqrt(np.sum(np.square(model_out - y_exp))))
            errors.append(error)
            if it % 30 == 0:
                print("model:\t{}  \texpected:\t{},  \terror: \t{}".format(model_out, y_exp, error), flush=True)
            it += 1

        test_batch_x, test_batch_y = data_picker.test_batch()

    mean_error = np.mean(errors)
    std_error = np.std(errors)
    max_error = np.max(errors)
    print("Mean error: {}, std: {}, max: {}".format(mean_error, std_error, max_error), flush=True)
    result = {
        "errors": json.dumps(errors),
        "mean": mean_error,
        "std": std_error,
        "max": max_error,
    }
    return result


def train(training_iters, save_step, epoch_size, img_size_x, img_size_y, dropout, conv_networks_dicts,
          full_connected_network_dicts, optimizer_type, loss_fun, data_picker: Data_picker, model_file: str, channels=3, **kwargs):

    n_input = img_size_x * img_size_y

    # tf graph input, output...
    x = tf.placeholder(tf.float32, [None, n_input * channels])
    y = tf.placeholder(tf.float32, [None, 2])
    keep_prob = tf.placeholder(tf.float32)  # dropout (keep probability)

    conv_network_variables_dicts, conv_out_size = init_conv_variables(conv_networks_dicts, img_size_x, img_size_y, channels)
    fc_network_variables_dicts = init_fc_variables(full_connected_network_dicts, conv_out_size)
    pred = \
        conv_net(x, conv_network_variables_dicts, fc_network_variables_dicts, conv_out_size, keep_prob, img_size_x,
                 img_size_y, channels)

    loss = loss_fun(pred, y)
    # loss_2 = tf.reduce_mean(tf.sqrt(tf.reduce_sum(tf.square(pred - y), 1)))
    optimizer = optimizer_type.minimize(loss)

    init = tf.global_variables_initializer()
    losses = list()
    saver = tf.train.Saver()
    # model_file = "./modele/first/model.cktp"

    with tf.Session() as sess:
        sess.run(init)
        step = 0
        epoch = 0
        start_epoch = dt.datetime.now()

        while step <= training_iters:
            batch_xs, batch_ys = data_picker.data_batch(step)

            start_op = dt.datetime.now()
            sess.run(optimizer, feed_dict={x: batch_xs, y: batch_ys, keep_prob: dropout})
            end_op = dt.datetime.now()
            print("#{} opt step {} {} takes {}".format(step, start_op, end_op, end_op - start_op), flush=True)


            if step % epoch_size == 0:
                batch_loss = sess.run(loss, feed_dict={x: batch_xs, y: batch_ys, keep_prob: 1.})
                print("Iter: {} ({} epoch), batch loss = {}".format(step, epoch, batch_loss), flush=True)
                losses.append(batch_loss)
                epoch += 1

            step += 1
            if step % save_step == 0:
                saved = saver.save(sess, model_file)

        end_epoch = dt.datetime.now()
        print("Optimization Finished, end={} duration={}".format(end_epoch, end_epoch - start_epoch), flush=True)

        return {**test_model(sess, data_picker, pred, x, keep_prob), **{"model_file": model_file}}
