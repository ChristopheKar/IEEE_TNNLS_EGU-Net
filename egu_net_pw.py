
#import library
import os
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
import scipy.io as spio
from tf_utils import random_mini_batches, convert_to_one_hot
from tensorflow.python.framework import ops


def create_placeholders(n_x1, n_x2, n_y):
    keep_prob = tf.placeholder(tf.float32)
    is_training = tf.placeholder_with_default(True, shape=())
    x_pure = tf.placeholder(tf.float32,  [None, n_x1], name="x_pure")
    x_mixed = tf.placeholder(tf.float32,  [None, n_x2], name="x_mixed")
    y = tf.placeholder(tf.float32, [None, n_y], name="Y")
    return x_pure, x_mixed, y, is_training, keep_prob


def initialize_parameters(in_channels=224, n_endmembers=5, seed=1):

    tf.set_random_seed(seed)

    xavier_init = tf.contrib.layers.xavier_initializer()
    zero_init = tf.zeros_initializer()

    x_w1 = tf.get_variable("x_w1", [in_channels, 256], initializer=xavier_init)
    x_b1 = tf.get_variable("x_b1", [256], initializer=zero_init)

    x_w2 = tf.get_variable("x_w2", [256,128], initializer=xavier_init)
    x_b2 = tf.get_variable("x_b2", [128], initializer=zero_init)

    x_w3 = tf.get_variable("x_w3", [128,32], initializer=xavier_init)
    x_b3 = tf.get_variable("x_b3", [32], initializer=zero_init)

    x_w4 = tf.get_variable("x_w4", [32, n_endmembers], initializer=xavier_init)
    x_b4 = tf.get_variable("x_b4", [n_endmembers], initializer=zero_init)

    x_dew1 = tf.get_variable("x_dew1", [n_endmembers, 32], initializer=xavier_init)
    x_deb1 = tf.get_variable("x_deb1", [32], initializer=zero_init)

    x_dew2 = tf.get_variable("x_dew2", [32,128], initializer=xavier_init)
    x_deb2 = tf.get_variable("x_deb2", [128], initializer=zero_init)

    x_dew3 = tf.get_variable("x_dew3", [128,256], initializer=xavier_init)
    x_deb3 = tf.get_variable("x_deb3", [256], initializer=zero_init)

    x_dew4 = tf.get_variable("x_dew4", [256, in_channels], initializer=xavier_init)
    x_deb4 = tf.get_variable("x_deb4", [in_channels], initializer=zero_init)

    parameters = {
        "x_w1": x_w1,
        "x_b1": x_b1,
        "x_w2": x_w2,
        "x_b2": x_b2,
        "x_w3": x_w3,
        "x_b3": x_b3,
        "x_w4": x_w4,
        "x_b4": x_b4,
        "x_dew1": x_dew1,
        "x_deb1": x_deb1,
        "x_dew2": x_dew2,
        "x_deb2": x_deb2,
        "x_dew3": x_dew3,
        "x_deb3": x_deb3,
        "x_dew4": x_dew4,
        "x_deb4": x_deb4}

    return parameters


def model(x_pure, x_mixed, parameters, is_training, keep_prob, momentum=0.9):

    with tf.name_scope("x_layer_1"):
        x_pure_z1 = tf.matmul(x_pure, parameters['x_w1']) + parameters['x_b1']
        x_pure_z1_bn = tf.layers.batch_normalization(
            x_pure_z1, axis=1,
            momentum=momentum, training=is_training, name='l1')
        x_pure_z1_do = tf.nn.dropout(x_pure_z1_bn, keep_prob)
        x_pure_a1 = tf.nn.tanh(x_pure_z1_do)

        x_mixed_z1 = tf.matmul(x_mixed, parameters['x_w1']) + parameters['x_b1']
        x_mixed_z1_bn = tf.layers.batch_normalization(
            x_mixed_z1, axis=1,
            momentum=momentum, training=is_training,
            name='l1', reuse=True)
        x_mixed_z1_do = tf.nn.dropout(x_mixed_z1_bn, keep_prob)
        x_mixed_a1 = tf.nn.tanh(x_mixed_z1_do)

    with tf.name_scope("x_layer_2"):
        x_pure_z2 = tf.matmul(x_pure_a1, parameters['x_w2']) + parameters['x_b2']
        x_pure_z2_bn = tf.layers.batch_normalization(
            x_pure_z2, axis=1,
            momentum=momentum, training=is_training, name='l2')
        x_pure_a2 = tf.nn.tanh(x_pure_z2_bn)

        x_mixed_z2 = tf.matmul(x_mixed_a1, parameters['x_w2']) + parameters['x_b2']
        x_mixed_z2_bn = tf.layers.batch_normalization(
            x_mixed_z2, axis=1,
            momentum=momentum, training=is_training,
            name='l2', reuse=True)
        x_mixed_a2 = tf.nn.tanh(x_mixed_z2_bn)

    with tf.name_scope("x_layer_3"):
        x_pure_z3 = tf.matmul(x_pure_a2, parameters['x_w3']) + parameters['x_b3']
        x_pure_z3_bn = tf.layers.batch_normalization(
            x_pure_z3, axis=1,
            momentum=momentum, training=is_training, name='l3')
        x_pure_a3 = tf.nn.relu(x_pure_z3_bn)

        x_mixed_z3 = tf.matmul(x_mixed_a2, parameters['x_w3']) + parameters['x_b3']
        x_mixed_z3_bn = tf.layers.batch_normalization(
            x_mixed_z3, axis=1,
            momentum=momentum, training=is_training,
            name='l3', reuse=True)
        x_mixed_a3 = tf.nn.relu(x_mixed_z3_bn)

    with tf.name_scope("x_layer_4"):
        x_pure_z4 = tf.add(tf.matmul(x_pure_a3, parameters['x_w4']), parameters['x_b4'])
        abundances_pure = tf.nn.softmax(x_pure_z4)

        x_mixed_z4 = tf.add(tf.matmul(x_mixed_a3, parameters['x_w4']), parameters['x_b4'])
        abundances_mixed = tf.nn.softmax(x_mixed_z4)

    with tf.name_scope("x_de_layer_1"):
        x_mixed_de_z1 = tf.matmul(abundances_mixed, parameters['x_dew1']) + parameters['x_deb1']
        x_mixed_de_z1_bn = tf.layers.batch_normalization(
            x_mixed_de_z1, axis=1,
            momentum=momentum, training=is_training)
        x_mixed_de_a1 = tf.nn.sigmoid(x_mixed_de_z1_bn)

    with tf.name_scope("x_de_layer_2"):
        x_mixed_de_z2 = tf.matmul(x_mixed_de_a1, parameters['x_dew2']) + parameters['x_deb2']
        x_mixed_de_z2_bn = tf.layers.batch_normalization(
            x_mixed_de_z2, axis=1,
            momentum=momentum, training=is_training)
        x_mixed_de_a2 = tf.nn.sigmoid(x_mixed_de_z2_bn)

    with tf.name_scope("x_de_layer_3"):
        x_mixed_de_z3 = tf.matmul(x_mixed_de_a2, parameters['x_dew3']) + parameters['x_deb3']
        x_mixed_de_z3_bn = tf.layers.batch_normalization(
            x_mixed_de_z3, axis=1,
            momentum=momentum, training=is_training)
        x_mixed_de_a3 = tf.nn.sigmoid(x_mixed_de_z3_bn)

    with tf.name_scope("x_de_layer_4"):
        x_mixed_de_z4 = tf.matmul(x_mixed_de_a3, parameters['x_dew4']) + parameters['x_deb4']
        x_mixed_de_z4_bn = tf.layers.batch_normalization(
            x_mixed_de_z4, axis=1,
            momentum=momentum, training=is_training)
        x_mixed_de_a4 = tf.nn.sigmoid(x_mixed_de_z4_bn)

    l2_loss =  tf.nn.l2_loss(parameters['x_w1'])
    l2_loss += tf.nn.l2_loss(parameters['x_w2'])
    l2_loss += tf.nn.l2_loss(parameters['x_w3'])
    l2_loss += tf.nn.l2_loss(parameters['x_w4'])
    l2_loss += tf.nn.l2_loss(parameters['x_dew1'])
    l2_loss += tf.nn.l2_loss(parameters['x_dew2'])
    l2_loss += tf.nn.l2_loss(parameters['x_dew3'])
    l2_loss += tf.nn.l2_loss(parameters['x_dew4'])

    return x_pure_z4, abundances_mixed, x_mixed_de_a4, l2_loss, abundances_pure, abundances_mixed


def optimize(y_est, y_re, r1, r2, l2_loss, reg, learning_rate, global_step):

    with tf.name_scope("cost"):
        cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(
            logits=y_est, labels=y_re))
        cost += reg*l2_loss
        cost += 1*tf.reduce_mean(tf.pow(r1 - r2, 2))

    with tf.name_scope("optimization"):
        update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)

    with tf.control_dependencies(update_ops):
        optimizer = tf.train.AdamOptimizer(
            learning_rate=learning_rate).minimize(
                cost, global_step=global_step)
        optimizer = tf.group([optimizer, update_ops])

    return cost, optimizer

def train(
    x_pure_set, x_mixed_set,
    y_train, y_test,
    in_channels=224, n_endmembers=5,
    learning_rate_base=0.1, beta_reg=0.005,
    num_epochs=200, minibatch_size=8000,
    seed=1, print_cost=True):

    ops.reset_default_graph()
    tf.set_random_seed(seed)
    (m, n_x1) = x_pure_set.shape
    (m1, n_x2) = x_mixed_set.shape
    (m, n_y) = y_train.shape

    costs = []
    costs_dev = []
    train_acc = []
    val_acc = []

    x_train_pure, x_train_mixed, y, is_training, keep_prob = create_placeholders(n_x1, n_x2, n_y)

    parameters = initialize_parameters(
        in_channels=in_channels, n_endmembers=n_endmembers, seed=seed)

    with tf.name_scope("network"):
        res = model(
            x_train_pure, x_train_mixed,
            parameters, is_training, keep_prob)
        x_pure_layer = res[0]
        x_mixed_layer = res[1]
        x_mixed_de_layer = res[2]
        l2_loss = res[3]
        abundances_pure = res[4]
        abundances_mixed = res[5]

    global_step = tf.Variable(0, trainable=False)
    learning_rate = tf.train.exponential_decay(
        learning_rate_base, global_step, m/minibatch_size, 0.99)

    with tf.name_scope("optimization"):
        cost, optimizer = optimize(
            x_pure_layer,
            y,
            x_mixed_de_layer,
            x_train_mixed,
            l2_loss,
            beta_reg,
            learning_rate,
            global_step)

    with tf.name_scope("metrics"):
        accuracy = tf.losses.absolute_difference(
            labels=y, predictions=abundances_pure)

    init = tf.global_variables_initializer()

    with tf.Session() as sess:

        sess.run(init)

        # Do the training loop
        for epoch in range(num_epochs):
            epoch_cost = 0.
            epoch_acc = 0.
            # number of minibatches of size minibatch_size in the train set
            num_minibatches = int(m1 / minibatch_size)
            seed = seed + 1
            minibatches = random_mini_batches(
                x_pure_set, x_mixed_set, y_train, minibatch_size, seed)
            for minibatch in minibatches:

                # Select a minibatch
                (batch_x1, batch_x2, batch_y) = minibatch
                _, minibatch_cost, minibatch_acc = sess.run(
                    [optimizer, cost, accuracy],
                    feed_dict={
                        x_train_pure: batch_x1,
                        x_train_mixed: batch_x2,
                        y: batch_y,
                        is_training: True,
                        keep_prob: 0.9
                    })
                epoch_cost += minibatch_cost
                epoch_acc += minibatch_acc

            epoch_cost_f = epoch_cost / (num_minibatches + 1)
            epoch_acc_f = epoch_acc / (num_minibatches + 1)


            abund, re, epoch_cost_dev, epoch_acc_dev = sess.run(
                [abundances_pure, x_mixed_de_layer, cost, accuracy],
                feed_dict={
                    x_train_pure: x_mixed_set,
                    x_train_mixed: x_mixed_set,
                    y: y_test,
                    is_training: True,
                    keep_prob: 1})

            if ((print_cost) and (epoch % 5 == 0)):
                print((
                    'epoch {:d}: Train_loss: {:f}, '
                    'Val_loss: {:f}, '
                    'Train_acc: {:f}, '
                    'Val_acc: {:f}').format(
                        epoch, epoch_cost_f, epoch_cost_dev,
                        epoch_acc_f, epoch_acc_dev))

            if ((print_cost) and (epoch % 1 == 0)):
                costs.append(epoch_cost_f)
                train_acc.append(epoch_acc_f)
                costs_dev.append(epoch_cost_dev)
                val_acc.append(epoch_acc_dev)


        # plot the cost
        plt.plot(np.squeeze(costs))
        plt.plot(np.squeeze(costs_dev))
        plt.ylabel('cost')
        plt.xlabel('iterations (per tens)')
        plt.title("Learning rate =" + str(learning_rate))
        plt.show()
        # plot the accuracy
        plt.plot(np.squeeze(train_acc))
        plt.plot(np.squeeze(val_acc))
        plt.ylabel('accuracy')
        plt.xlabel('iterations (per tens)')
        plt.title("Learning rate =" + str(learning_rate))
        plt.show()
        # lets save the parameters in a variable
        parameters = sess.run(parameters)
        print("Parameters have been trained!")
        return parameters, val_acc, abund


if __name__ == '__main__':

    # Load data
    Pure_TrSet = spio.loadmat('data/tnnls/Pure_TrSet.mat')
    Mixed_TrSet = spio.loadmat('data/tnnls/Mixed_TrSet.mat')

    TrLabel = spio.loadmat('data/tnnls/TrLabel.mat')
    TeLabel = spio.loadmat('data/tnnls/TeLabel.mat')

    Pure_TrSet = Pure_TrSet['Pure_TrSet']
    Mixed_TrSet = Mixed_TrSet['Mixed_TrSet']
    TrLabel = TrLabel['TrLabel']
    TeLabel = TeLabel['TeLabel']

    Y_train = TrLabel
    Y_test = TeLabel

    in_channels = 224
    n_endmembers = 5

    # Train model
    parameters, val_acc, abund = train(
        Pure_TrSet, Mixed_TrSet,
        Y_train, Y_test,
        in_channels=in_channels,
        n_endmembers=n_endmembers)

    # Save results
    os.makedirs('results', exist_ok=True)
    spio.savemat('results/abund_pw.mat', {'abund': abund})
