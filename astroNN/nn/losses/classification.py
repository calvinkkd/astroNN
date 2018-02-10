# -----------------------------------------------------------------------#
#   astroNN.models.losses.classification: losses function for classification
# ----------------------------------------------------------------------#
import tensorflow as tf
from tensorflow.contrib import distributions
from tensorflow.python.framework import ops
from tensorflow.python.ops import array_ops
from tensorflow.python.ops import math_ops
from keras.backend import epsilon

from astroNN import MAGIC_NUMBER


def astronn_sigmoid_cross_entropy_with_logits(_sentinel=None, labels=None, logits=None, name=None):
    """
    NAME: astronn_sigmoid_cross_entropy_with_logits
    PURPOSE: Computes sigmoid cross entropy given `logits`.
             # Measures the probability error in discrete classification tasks in which each
             class is independent and not mutually exclusive.  For instance, one could
             perform multilabel classification where a picture can contain both an elephant
             and a dog at the same time.
    INPUT:
    OUTPUT:
          A `Tensor` of the same shape as `logits` with the componentwise
          logistic losses.
    HISTORY:
        2018-Jan-18 - Written - Henry Leung (University of Toronto)
    """
    with ops.name_scope(name, "logistic_loss", [logits, labels]) as name:
        logits = ops.convert_to_tensor(logits, name="logits")
        labels = ops.convert_to_tensor(labels, name="labels")
        try:
            labels.get_shape().merge_with(logits.get_shape())
        except ValueError:
            raise ValueError("logits and labels must have the same shape ({0!s} vs {0!s})".format(logits.get_shape(),
                                                                                                  labels.get_shape()))

        zeros = array_ops.zeros_like(logits, dtype=logits.dtype)
        cond = (logits >= zeros)
        relu_logits = array_ops.where(cond, logits, zeros)
        neg_abs_logits = array_ops.where(cond, -logits, logits)

        magic_cond = (labels == MAGIC_NUMBER)  # To deal with missing labels
        return array_ops.where(magic_cond, zeros,
                               math_ops.add(relu_logits - logits * labels, math_ops.log1p(math_ops.exp(neg_abs_logits)))
                               , name=name)


def categorical_cross_entropy(y_true, y_pred, from_logits=False):
    """
    NAME: astronn_categorical_crossentropy
    PURPOSE: Categorical crossentropy between an output tensor and a target tensor.
            # Note: tf.nn.softmax_cross_entropy_with_logits
            # expects logits, Keras expects probabilities.
    INPUT:
        y_true: A tensor of the same shape as `output`.
        y_pred: A tensor resulting from a softmax (unless `from_logits` is True, in which case `output` is expected
        to be the logits).
        from_logits: Boolean, whether `output` is the result of a softmax, or is a tensor of logits.
    OUTPUT:
        Output tensor
    HISTORY:
        2018-Jan-14 - Written - Henry Leung (University of Toronto)
    """
    if not from_logits:
        # Deal with magic number first
        y_true = tf.where(tf.equal(y_true, MAGIC_NUMBER), tf.zeros_like(y_true), y_true)
        # scale preds so that the class probas of each sample sum to 1
        y_pred /= tf.reduce_sum(y_pred, len(y_pred.get_shape()) - 1, True)
        # manual computation of crossentropy
        epsilon_tensor = tf.convert_to_tensor(epsilon(), y_pred.dtype.base_dtype)
        y_pred = tf.clip_by_value(y_pred, epsilon_tensor, 1. - epsilon_tensor)
        return - tf.reduce_sum(y_true * tf.log(y_pred), len(y_pred.get_shape()) - 1)
    else:
        try:
            return tf.nn.softmax_cross_entropy_with_logits_v2(labels=y_true, logits=y_pred)
        except AttributeError or ImportError:
            return tf.nn.softmax_cross_entropy_with_logits(labels=y_true, logits=y_pred)


def binary_cross_entropy(y_true, y_pred, from_logits=False):
    """
    NAME: binary_crossentropy
    PURPOSE: Binary crossentropy between an output tensor and a target tensor.
            # Note: tf.nn.softmax_cross_entropy_with_logits
            # expects logits, Keras expects probabilities.
    INPUT:
        y_true: A tensor of the same shape as `output`.
        y_pred: A tensor resulting from a softmax (unless `from_logits` is True, in which case `output` is expected
        to be the logits).
        from_logits: Boolean, whether `output` is the result of a softmax, or is a tensor of logits.
    OUTPUT:
        Output tensor
    HISTORY:
        2018-Jan-14 - Written - Henry Leung (University of Toronto)
    """
    # Note: tf.nn.sigmoid_cross_entropy_with_logits
    # expects logits, Keras expects probabilities.
    if not from_logits:
        # Deal with magic number first
        y_true = tf.where(tf.equal(y_true, MAGIC_NUMBER), tf.zeros_like(y_true), y_true)
        # transform back to logits
        epsilon_tensor = tf.convert_to_tensor(epsilon(), y_pred.dtype.base_dtype)
        y_pred = tf.clip_by_value(y_pred, epsilon_tensor, 1 - epsilon_tensor)
        y_pred = tf.log(y_pred / (1 - y_pred))

    return tf.reduce_mean(astronn_sigmoid_cross_entropy_with_logits(labels=y_true, logits=y_pred), axis=-1)


def bayesian_crossentropy_wrapper(from_logits=True):
    """
    NAME: bayesian_crossentropy_wrapper
    PURPOSE: Binary crossentropy between an output tensor and a target tensor for Bayesian Neural Network
            # Note: tf.nn.softmax_cross_entropy_with_logits
            # expects logits, Keras expects probabilities.
    INPUT:
        y_true: A tensor of the same shape as `output`.
        y_pred: A tensor resulting from a softmax (unless `from_logits` is True, in which case `output` is expected
        to be the logits).
        from_logits: Boolean, whether `output` is the result of a softmax, or is a tensor of logits.
    OUTPUT:
        Output tensor
    HISTORY:
        2018-Feb-09 - Written - Henry Leung (University of Toronto)
    """
    def bayesian_crossentropy(y_true, y_pred):
        T = 25
        num_classes = tf.shape(y_pred)[1]
        std = tf.sqrt(y_pred)
        variance = y_pred[:, num_classes]
        variance_depressor = tf.exp(variance) - tf.ones_like(variance)
        pred = y_pred[:, 0:num_classes]
        undistorted_loss = categorical_cross_entropy(pred, y_true, from_logits=from_logits)
        iterable = tf.ones(T)
        norm_dist = tf.random_normal(shape=tf.shape(std), mean=tf.zeros_like(std), stddev=std)
        monte_carlo_results = tf.map_fn(
            gaussian_crossentropy(y_true, pred, norm_dist, undistorted_loss, num_classes), iterable,
            name='monte_carlo_results')

        variance_loss = tf.reduce_mean(monte_carlo_results, axis=0) * undistorted_loss

        return variance_loss + undistorted_loss + variance_depressor

    return bayesian_crossentropy


def gaussian_crossentropy(true, pred, dist, undistorted_loss, num_classes):
    """
    NAME: gaussian_crossentropy
    PURPOSE: gaussian
    INPUT:
    OUTPUT:
        Output tensor
    HISTORY:
        2018-Feb-09 - Written - Henry Leung (University of Toronto)
    """
    def map_fn(i):
        std_samples = tf.transpose(dist.sample(num_classes))
        distorted_loss = categorical_cross_entropy(pred + std_samples, true, from_logits=True)
        diff = undistorted_loss - distorted_loss
        return -tf.nn.elu(diff)

    return map_fn