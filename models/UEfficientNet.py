## https://www.kaggle.com/meaninglesslives/nested-unet-with-efficientnet-encoder

import tensorflow as tf
from tensorflow import keras
#from efficientnet import EfficientNetB4
from efficientnet.tfkeras import EfficientNetB4
import numpy as np


def convolution_block(x, filters, size, strides=(1,1), padding='same', activation=True):
    x = keras.layers.Conv2D(filters, size, strides=strides, padding=padding)(x)
    x = keras.layers.BatchNormalization()(x)
    if activation == True:
        x = keras.layers.LeakyReLU(alpha=0.1)(x)
    return x

def residual_block(blockInput, num_filters=16):
    x = keras.layers.LeakyReLU(alpha=0.1)(blockInput)
    x = keras.layers.BatchNormalization()(x)
    blockInput = keras.layers.BatchNormalization()(blockInput)
    x = convolution_block(x, num_filters, (3,3) )
    x = convolution_block(x, num_filters, (3,3), activation=False)
    x = keras.layers.Add()([x, blockInput])
    return x


def UEfficientNetB4(input_shape=(256, 256, 3), dropout_rate=0.5,imagenet_weights='imagenet'):
    backbone = EfficientNetB4(weights=imagenet_weights,include_top=False,input_shape=input_shape)
    input = backbone.input
    start_neurons = 8

    conv4 = backbone.layers[342].output
    conv4 = keras.layers.LeakyReLU(alpha=0.1)(conv4)
    pool4 = keras.layers.MaxPooling2D((2, 2))(conv4)
    pool4 = keras.layers.Dropout(dropout_rate)(pool4)

    # Middle
    convm = keras.layers.Conv2D(start_neurons * 32, (3, 3), activation=None, padding="same", name='conv_middle')(pool4)
    convm = residual_block(convm, start_neurons * 32)
    convm = residual_block(convm, start_neurons * 32)
    convm = keras.layers.LeakyReLU(alpha=0.1)(convm)

    deconv4 = keras.layers.Conv2DTranspose(start_neurons * 16, (3, 3), strides=(2, 2), padding="same")(convm)
    deconv4_up1 = keras.layers.Conv2DTranspose(start_neurons * 16, (3, 3), strides=(2, 2), padding="same")(deconv4)
    deconv4_up2 = keras.layers.Conv2DTranspose(start_neurons * 16, (3, 3), strides=(2, 2), padding="same")(deconv4_up1)
    deconv4_up3 = keras.layers.Conv2DTranspose(start_neurons * 16, (3, 3), strides=(2, 2), padding="same")(deconv4_up2)
    uconv4 = keras.layers.concatenate([deconv4, conv4])
    uconv4 = keras.layers.Dropout(dropout_rate)(uconv4)

    uconv4 = keras.layers.Conv2D(start_neurons * 16, (3, 3), activation=None, padding="same")(uconv4)
    uconv4 = residual_block(uconv4, start_neurons * 16)
    #     uconv4 = residual_block(uconv4,start_neurons * 16)
    uconv4 = keras.layers.LeakyReLU(alpha=0.1)(uconv4)  # conv1_2

    deconv3 = keras.layers.Conv2DTranspose(start_neurons * 8, (3, 3), strides=(2, 2), padding="same")(uconv4)
    deconv3_up1 = keras.layers.Conv2DTranspose(start_neurons * 8, (3, 3), strides=(2, 2), padding="same")(deconv3)
    deconv3_up2 = keras.layers.Conv2DTranspose(start_neurons * 8, (3, 3), strides=(2, 2), padding="same")(deconv3_up1)
    conv3 = backbone.layers[154].output
    uconv3 = keras.layers.concatenate([deconv3, deconv4_up1, conv3])
    uconv3 = keras.layers.Dropout(dropout_rate)(uconv3)

    uconv3 = keras.layers.Conv2D(start_neurons * 8, (3, 3), activation=None, padding="same")(uconv3)
    uconv3 = residual_block(uconv3, start_neurons * 8)
    #     uconv3 = residual_block(uconv3,start_neurons * 8)
    uconv3 = keras.layers.LeakyReLU(alpha=0.1)(uconv3)

    deconv2 = keras.layers.Conv2DTranspose(start_neurons * 4, (3, 3), strides=(2, 2), padding="same")(uconv3)
    deconv2_up1 = keras.layers.Conv2DTranspose(start_neurons * 4, (3, 3), strides=(2, 2), padding="same")(deconv2)
    conv2 = backbone.layers[89].output #92=>89
    uconv2 = keras.layers.concatenate([deconv2, deconv3_up1, deconv4_up2, conv2])

    uconv2 = keras.layers.Dropout(0.1)(uconv2)
    uconv2 = keras.layers.Conv2D(start_neurons * 4, (3, 3), activation=None, padding="same")(uconv2)
    uconv2 = residual_block(uconv2, start_neurons * 4)
    #     uconv2 = residual_block(uconv2,start_neurons * 4)
    uconv2 = keras.layers.LeakyReLU(alpha=0.1)(uconv2)

    deconv1 = keras.layers.Conv2DTranspose(start_neurons * 2, (3, 3), strides=(2, 2), padding="same")(uconv2)
    conv1 = backbone.layers[30].output
    uconv1 = keras.layers.concatenate([deconv1, deconv2_up1, deconv3_up2, deconv4_up3, conv1])

    uconv1 = keras.layers.Dropout(0.1)(uconv1)
    uconv1 = keras.layers.Conv2D(start_neurons * 2, (3, 3), activation=None, padding="same")(uconv1)
    uconv1 = residual_block(uconv1, start_neurons * 2)
    #     uconv1 = residual_block(uconv1,start_neurons * 2)
    uconv1 = keras.layers.LeakyReLU(alpha=0.1)(uconv1)

    uconv0 = keras.layers.Conv2DTranspose(start_neurons * 1, (3, 3), strides=(2, 2), padding="same")(uconv1)
    uconv0 = keras.layers.Dropout(0.1)(uconv0)
    uconv0 = keras.layers.Conv2D(start_neurons * 1, (3, 3), activation=None, padding="same")(uconv0)
    uconv0 = residual_block(uconv0, start_neurons * 1)
    #     uconv0 = residual_block(uconv0,start_neurons * 1)
    uconv0 = keras.layers.LeakyReLU(alpha=0.1)(uconv0)
    uconv0 = keras.layers.Dropout(dropout_rate / 2)(uconv0)

    d1=keras.layers.UpSampling2D(size=(2,2))(uconv0)
    d1 = keras.layers.Conv2D(1, (3, 3), padding="same", activation=None, use_bias=False)(d1)
    d11=keras.layers.Activation('sigmoid',name='d1')(d1)

    d2 = keras.layers.UpSampling2D(size=(4, 4))(uconv1)
    d2 = keras.layers.Conv2D(1, (3, 3), padding="same", activation=None, use_bias=False)(d2)
    d22 = keras.layers.Activation('sigmoid', name='d2')(d2)

    d3 = keras.layers.UpSampling2D(size=(8, 8))(uconv2)
    d3 = keras.layers.Conv2D(1, (3, 3), padding="same", activation=None, use_bias=False)(d3)
    d33 = keras.layers.Activation('sigmoid', name='d3')(d3)

    d4 = keras.layers.UpSampling2D(size=(16, 16))(uconv3)
    d4 = keras.layers.Conv2D(1, (3, 3), padding="same", activation=None, use_bias=False)(d4)
    d44 = keras.layers.Activation('sigmoid', name='d4')(d4)

    d5 = keras.layers.UpSampling2D(size=(32, 32))(uconv4)
    d5 = keras.layers.Conv2D(1, (3, 3), padding="same", activation=None, use_bias=False)(d5)
    d55 = keras.layers.Activation('sigmoid', name='d5')(d5)

    d = keras.layers.concatenate([d1, d2, d3, d4, d5,input])
    d = keras.layers.Conv2D(1, kernel_size=3, activation=None, padding='same', use_bias=False)(d)
    d = keras.layers.Activation('sigmoid', name='d')(d)
    model = keras.models.Model(inputs=input,outputs=[d,d11,d22,d33,d44,d55])
    #model.name = 'u-xception'
    '''
    Total params: 10,501,068
    Trainable params: 10,435,420
    Non-trainable params: 65,648
    '''
    return model


def get_iou_vector(A, B):
    # Numpy version
    batch_size = A.shape[0]
    metric = 0.0
    for batch in range(batch_size):
        t, p = A[batch], B[batch]
        true = np.sum(t)
        pred = np.sum(p)

        # deal with empty mask first
        if true == 0:
            metric += (pred == 0)
            continue

        # non empty mask case.  Union is never empty
        # hence it is safe to divide by its number of pixels
        intersection = np.sum(t * p)
        union = true + pred - intersection
        iou = intersection / union

        # iou metrric is a stepwise approximation of the real iou over 0.5
        iou = np.floor(max(0, (iou - 0.45) * 20)) / 10

        metric += iou

    # teake the average over all images in batch
    metric /= batch_size
    return metric

##
def IOU(label, pred):
    # Tensorflow version
    return tf.py_function (get_iou_vector, [label, pred > 0.5], tf.float64)


def dice_loss(y_true, y_pred):
    smooth = 1.
    y_true_f = keras.backend.flatten(y_true)
    y_pred_f = keras.backend.flatten(y_pred)
    intersection = y_true_f * y_pred_f
    score = (2. * keras.backend.sum(intersection) + smooth) / (keras.backend.sum(y_true_f) + keras.backend.sum(y_pred_f) + smooth)
    return 1. - score
##
def bce_dice_loss(y_true, y_pred):
    return keras.losses.binary_crossentropy(y_true, y_pred) + dice_loss(y_true, y_pred)

def bce_logdice_loss(y_true, y_pred):
    return keras.losses.binary_crossentropy(y_true, y_pred) - keras.backend.log(1. - dice_loss(y_true, y_pred))

#import tensorflow_addons as tfa
#tfa.losses.GIoULoss
