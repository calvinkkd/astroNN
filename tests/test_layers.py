import unittest

import numpy as np
import numpy.testing as npt
import tensorflow as tf

from astroNN.config import keras_import_manager
from astroNN.shared.nn_tools import gpu_memory_manage

keras = keras_import_manager()

Input = keras.layers.Input
Dense = keras.layers.Dense
Conv1D = keras.layers.Conv1D
Conv2D = keras.layers.Conv2D
Flatten = keras.layers.Flatten
Model = keras.models.Model

gpu_memory_manage()

# force the test to use CPU, using GPU will be much slower for such small test
sess = tf.Session(config=tf.ConfigProto(device_count={'GPU': 0}))
keras.backend.set_session(sess)


class LayerCase(unittest.TestCase):
    def test_MCDropout(self):
        print('==========MCDropout tests==========')
        from astroNN.nn.layers import MCDropout

        # Data preparation
        random_xdata = np.random.normal(0, 1, (100, 7514))
        random_ydata = np.random.normal(0, 1, (100, 25))

        input = Input(shape=[7514])
        dense = Dense(100)(input)
        b_dropout = MCDropout(0.2, name='dropout')(dense)
        output = Dense(25)(b_dropout)
        model = Model(inputs=input, outputs=output)
        model.compile(optimizer='sgd', loss='mse')

        model.fit(random_xdata, random_ydata, batch_size=128)

        print(model.get_layer('dropout').get_config())

        # make sure dropout is on even in testing phase
        x = model.predict(random_xdata)
        y = model.predict(random_xdata)
        npt.assert_equal(np.any(np.not_equal(x, y)), True)

    def test_MCGaussianDropout(self):
        print('==========MCGaussianDropout tests==========')
        from astroNN.nn.layers import MCGaussianDropout

        # Data preparation
        random_xdata = np.random.normal(0, 1, (100, 7514))
        random_ydata = np.random.normal(0, 1, (100, 25))

        input = Input(shape=[7514])
        dense = Dense(100)(input)
        b_dropout = MCGaussianDropout(0.2, name='dropout')(dense)
        output = Dense(25)(b_dropout)
        model = Model(inputs=input, outputs=output)
        model.compile(optimizer='sgd', loss='mse')

        model.fit(random_xdata, random_ydata, batch_size=128)

        print(model.get_layer('dropout').get_config())

        # make sure dropout is on even in testing phase
        x = model.predict(random_xdata)
        y = model.predict(random_xdata)
        npt.assert_equal(np.any(np.not_equal(x, y)), True)

    def test_ConcreteDropout(self):
        print('==========ConcreteDropout tests==========')
        from astroNN.nn.layers import MCConcreteDropout

        # Data preparation
        random_xdata = np.random.normal(0, 1, (100, 7514))
        random_ydata = np.random.normal(0, 1, (100, 25))

        input = Input(shape=[7514])
        dense = MCConcreteDropout(Dense(100), name='dropout')(input)
        output = Dense(25)(dense)
        model = Model(inputs=input, outputs=output)
        model.compile(optimizer='sgd', loss='mse')

        model.fit(random_xdata, random_ydata, batch_size=128)

        print(model.get_layer('dropout').get_config())

        # make sure dropout is on even in testing phase
        x = model.predict(random_xdata)
        y = model.predict(random_xdata)
        npt.assert_equal(np.any(np.not_equal(x, y)), True)

    def test_SpatialDropout1D(self):
        print('==========SpatialDropout1D tests==========')
        from astroNN.nn.layers import MCSpatialDropout1D

        # Data preparation
        random_xdata = np.random.normal(0, 1, (100, 7514, 1))
        random_ydata = np.random.normal(0, 1, (100, 25))

        input = Input(shape=[7514, 1])
        conv = Conv1D(kernel_initializer='he_normal', padding="same", filters=2, kernel_size=16)(input)
        dropout = MCSpatialDropout1D(0.2)(conv)
        flattened = Flatten()(dropout)
        output = Dense(25)(flattened)
        model = Model(inputs=input, outputs=output)
        model.compile(optimizer='sgd', loss='mse')

        model.fit(random_xdata, random_ydata, batch_size=128)

        # make sure dropout is on even in testing phase
        x = model.predict(random_xdata)
        y = model.predict(random_xdata)
        npt.assert_equal(np.any(np.not_equal(x, y)), True)

    def test_SpatialDropout12D(self):
        print('==========SpatialDropout2D tests==========')
        from astroNN.nn.layers import MCSpatialDropout2D

        # Data preparation
        random_xdata = np.random.normal(0, 1, (100, 28, 28, 1))
        random_ydata = np.random.normal(0, 1, (100, 25))

        input = Input(shape=[28, 28, 1])
        conv = Conv2D(kernel_initializer='he_normal', padding="same", filters=2, kernel_size=16)(input)
        dropout = MCSpatialDropout2D(0.2)(conv)
        flattened = Flatten()(dropout)
        output = Dense(25)(flattened)
        model = Model(inputs=input, outputs=output)
        model.compile(optimizer='sgd', loss='mse')

        model.fit(random_xdata, random_ydata, batch_size=128)

        # make sure dropout is on even in testing phase
        x = model.predict(random_xdata)
        y = model.predict(random_xdata)
        npt.assert_equal(np.any(np.not_equal(x, y)), True)

    def test_ErrorProp(self):
        print('==========MCDropout tests==========')
        from astroNN.nn.layers import ErrorProp

        # Data preparation
        random_xdata = np.random.normal(0, 1, (100, 7514))
        random_ydata = np.random.normal(0, 1, (100, 25))

        input = Input(shape=[7514])
        input_w_err = ErrorProp(input, name='error')(input)
        dense = Dense(100)(input_w_err)
        output = Dense(25)(dense)
        model = Model(inputs=input, outputs=output)
        model.compile(optimizer='sgd', loss='mse')

        model.fit(random_xdata, random_ydata, batch_size=128)

        print(model.get_layer('error').get_config())

        # make sure dropout is on even in testing phase
        x = model.predict(random_xdata)
        y = model.predict(random_xdata)
        npt.assert_equal(np.any(np.not_equal(x, y)), True)

    def test_MCBN(self):
        print('==========MCDropout tests==========')
        from astroNN.nn.layers import MCBatchNorm

        # Data preparation
        random_xdata = np.random.normal(0, 1, (100, 7514))
        random_ydata = np.random.normal(0, 1, (100, 25))

        input = Input(shape=[7514])
        dense = Dense(100)(input)
        b_dropout = MCBatchNorm(name='MCBN')(dense)
        output = Dense(25)(b_dropout)
        model = Model(inputs=input, outputs=output)
        model.compile(optimizer='sgd', loss='mse')

        model.fit(random_xdata, random_ydata, batch_size=128)

        print(model.get_layer('MCBN').get_config())

        # make sure dropout is on even in testing phase
        x = model.predict(random_xdata)
        y = model.predict(random_xdata)
        npt.assert_equal(np.any(np.not_equal(x, y)), False)


if __name__ == '__main__':
    unittest.main()
