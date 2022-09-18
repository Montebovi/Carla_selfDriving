import glob
import itertools
import math
import random
import keras.backend as K
import cv2
import keras.models
from keras.callbacks import ModelCheckpoint, EarlyStopping
import tensorflow as tf
import numpy as np
import os
from pathlib import Path

BATCH_SIZE = 32
DIRECTORIES = ["C:/_buttare/Town01_001", "C:/_buttare/Town01_002", "C:/_buttare/Town01_003", "C:/_buttare/Town01_004",
               "C:/_buttare/Town01_005", "C:/_buttare/Town01_006", "C:/_buttare/Town01_007", "C:/_buttare/Town01_008",
               "C:/_buttare/Town01_009"]
VALDIRECTORY = "C:/_buttare/Town02_005"

# eslusione GPU ############################################
# import os
# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
# import tensorflow as tf

def extract_image(file_name):
    return cv2.imread(file_name)


def find_files(pattern):
    files = []
    for file_name in glob.iglob(pattern, recursive=True):
        files.append(file_name)
    return files


def zeroFillFileNames(directories, folders):
    for aDir in directories:
        for f in folders:
            path = os.path.join(aDir, f + "/*.jpg")
            files = find_files(path)
            for aFile in files:
                fn = Path(aFile).stem
                if (len(fn) < 10):
                    fn10 = fn.zfill(10)
                    newName = aFile.replace(fn + ".", fn10 + ".")
                    # print(f" {aFile} --> {newName}")
                    os.rename(aFile, newName)


def loadFileNames(directories, folders):
    allFiles = {}
    for f in folders:
        allFiles[f] = []

    for aDir in directories:
        for f in folders:
            path = os.path.join(aDir, f + "/*.jpg")
            # print(path)
            files = find_files(path)
            files.sort()
            allFiles[f] = allFiles[f] + files

    return allFiles


def loadDataFromNpy(path, fieldname):
    outputFile = open(path, "br")
    outputs = []
    output_np = []
    while True:
        try:
            output = np.load(outputFile, allow_pickle=True)
            outputs.append(output)
        except:
            break
    for i in range(0, len(outputs)):
        if fieldname is None:
            output_np.append(outputs[i].flat[0])
        else:
            output_np.append(outputs[i].flat[0][fieldname])
        outputs[i] = None
    outputFile.close()
    return output_np


def loadVehicleData(paths):
    output_np = []
    for p in paths:
        p = os.path.join(p, "vehicleData.npy")
        out = loadDataFromNpy(p, "data")
        # print(f"Load vehicle data in [{p}] [len:{len(out)}]")
        output_np = list(itertools.chain(output_np, out))
    return output_np


def loadVehicleState(paths):
    data = []
    for p in paths:
        p = os.path.join(p, "vehicleState.npy")
        values = loadDataFromNpy(p, "speed_ms")
        data = list(itertools.chain(data, values))
    return data

def loadDataNav(paths):
    data = []
    for p in paths:
        p = os.path.join(p, "navigationData.npy")
        values = loadDataFromNpy(p, None)
        data = list(itertools.chain(data, values))
    for o in data:
        if o['dirDist'] is None:
            o['dirDist'] = 0
    return [ (o['dir'],o['dirDist']/(1+o['dirDist'])) for o in data]

def loadObstacleData(paths):
    data = []
    for p in paths:
        p = os.path.join(p, "obstacleSensor.npy")
        values = loadDataFromNpy(p, 'data')
        for i in range(0, len(values)-1):
            if math.isnan(values[i][1]):
                values[i][1] = 0
        # values = np.squeeze(values)
        data = list(itertools.chain(data, values))

    return data



# ######################################################################################################################
# percZeros: percentuale desiderata dei zero-steer sul totale
def reduceZerosSteer(filesCentral, filesLeft, filesRight,filesRgb,
                     x_vehicleState, x_dataNavigation,x_obstacle, y_vehicleData, percZeros):
    MAXZEROSTEER = 0.01
    listIdxZeros = []
    total = len(y_vehicleData)
    listSteer = [s[0] for s in y_vehicleData]
    listBrake = [s[2] for s in y_vehicleData]
    numZeros1 = len([s for s in range(0,len(listSteer)) if (abs(listSteer[s]) <= MAXZEROSTEER and listBrake[s] < 0.2)])
    print(numZeros1)
    numZeros = len([s for s in listSteer if abs(s) <= MAXZEROSTEER])
    attualPercentOfZeros = (1.0 * numZeros1) / total
    if attualPercentOfZeros <= percZeros:
        return filesCentral, filesLeft, filesRight, filesRgb, x_vehicleState, x_dataNavigation, x_obstacle, y_vehicleData

    toRemove = int((1.0 * numZeros1 - percZeros * total) / (1 - percZeros))

    for idx in range(0, total):
        steer = y_vehicleData[idx][0]
        brake = y_vehicleData[idx][2]
        if abs(steer) <= MAXZEROSTEER and brake < 0.2:
            listIdxZeros.append(idx)
    random.shuffle(listIdxZeros)
    listIdxZeros = listIdxZeros[0:toRemove]

    listIdxZeros.sort(reverse=True)
    for idx in range(0, toRemove):
        idxToRemove = listIdxZeros[idx]
        del filesCentral[idxToRemove]
        del filesLeft[idxToRemove]
        del filesRight[idxToRemove]
        del filesRgb[idxToRemove]
        x_vehicleState = np.delete(x_vehicleState, idxToRemove)
        del x_dataNavigation[idxToRemove]
        # x_obstacle = np.delete(x_obstacle, idxToRemove)
        del x_obstacle[idxToRemove]
        y_vehicleData = np.delete(y_vehicleData, idxToRemove, axis=0)

    return filesCentral, filesLeft, filesRight,filesRgb, x_vehicleState,x_dataNavigation, x_obstacle, y_vehicleData


def genPermutation(number):
    np.random.seed(42)
    indexes = np.random.permutation(number)
    return indexes

MAX_VELOCITY = 100

def generator(fileCentralNames, fileLeftNames, fileRightNames,filesRgb, vehicleState, dataNav,obstacleSensor, vehicleData, fn_image, batch_size=24):
    while 1:  # Loop forever so the generator never terminates
        num_samples = len(fileCentralNames)
        idxMap = genPermutation(num_samples)

        for offset in range(0, num_samples, batch_size):
            r = idxMap[offset:offset + batch_size]
            nomifileCentrals = [fileCentralNames[idx] for idx in r]
            nomifileLeft = [fileLeftNames[idx] for idx in r]
            nomifileRight = [fileRightNames[idx] for idx in r]
            nomifileRgb = [filesRgb[idx] for idx in r]

            x_imgC = [fn_image(x) / 255. for x in nomifileCentrals]
            x_imgL = [fn_image(x) / 255. for x in nomifileLeft]
            x_imgR = [fn_image(x) / 255. for x in nomifileRight]
            x_imgRGB = [fn_image(x) / 255. for x in nomifileRgb]

            x_vehicleState = [vehicleState[idx]/MAX_VELOCITY for idx in r]
            x_dataNav = [dataNav[idx] for idx in r]
            x_obstacleSensor = [[float(obstacleSensor[idx][0])/(1+abs(float(obstacleSensor[idx][0]))), float(obstacleSensor[idx][1])/(1+abs(float(obstacleSensor[idx][1])))] for idx in r]
            # x_obstacleSensor = [[float(obstacleSensor[idx][0])/(1+abs(float(obstacleSensor[idx][0]))),float(obstacleSensor[idx][1])] for idx in r]
            y_vehicleData = [vehicleData[idx] for idx in r]

            yield [np.array(x_imgC), np.array(x_imgL), np.array(x_imgR),np.array(x_imgRGB),
                   np.array(x_vehicleState),np.array(x_dataNav), np.array(x_obstacleSensor)], np.array(y_vehicleData)
            # yield [np.array(x_imgC), np.array(x_imgL), np.array(x_imgR), np.array(x_imgRGB),
            #        np.array(x_vehicleState), np.array(x_dataNav)], np.array(y_vehicleData)

            # yield [np.array(x_imgC), np.array(x_imgL), np.array(x_imgR), np.array(x_vehicleState), np.array(nomifileCentrals),np.array(nomifileLeft),np.array(nomifileRight)], np.array(y_vehicleData)


# #####################################################################################################################
# #####################################################################################################################
# #####################################################################################################################

cameraFiles = loadFileNames(DIRECTORIES, ["cameraCentral", "cameraLeft", "cameraRight", "cameraRgbCentral"])
val_cameraFiles = loadFileNames([VALDIRECTORY], ["cameraCentral", "cameraLeft", "cameraRight", "cameraRgbCentral"])

print("Total cameras data:")
for cam in ["cameraCentral", "cameraLeft", "cameraRight", "cameraRgbCentral"]:
    print(f"{cam}: {len(cameraFiles[cam])}")
vehicleData = loadVehicleData(DIRECTORIES)
print(f"Total vehicle data: {len(vehicleData)}")

x_vehicleState = loadVehicleState(DIRECTORIES)
y_vehicleData = loadVehicleData(DIRECTORIES)
x_dataNav = loadDataNav(DIRECTORIES)
x_obstacleSensor = loadObstacleData(DIRECTORIES)


valx_vehicleState = loadVehicleState([VALDIRECTORY])
valy_vehicleData = loadVehicleData([VALDIRECTORY])
valx_dataNav = loadDataNav([VALDIRECTORY])
valx_obstacleSensor = loadObstacleData([VALDIRECTORY])

from keras.utils import plot_model
from keras.models import Model
from keras.layers import Input
from keras.layers import Dense
from keras.layers import Dropout
from keras.layers import Flatten
from keras.layers.convolutional import Conv2D
from keras.layers.pooling import MaxPooling2D, AveragePooling2D
from keras.layers import concatenate
from keras.losses import mse
from keras.optimizers import Adam
from keras.models import Model, Sequential


def createConv(inputCam, convFilters):
    conv11 = Conv2D(4, kernel_size=4, strides=(2, 2), activation='elu')(inputCam)
    pool11 = MaxPooling2D(pool_size=(3, 3))(conv11)
    #dropout11 = Dropout(0.25)(pool11)

    conv12 = Conv2D(8, kernel_size=3, strides=(1, 1), padding="same", activation='relu')(pool11)
    pool12 = MaxPooling2D(pool_size=(2, 2))(conv12)

    conv13 = Conv2D(16, kernel_size=3, strides=(2, 2), padding="same", activation='relu')(pool12)
    pool13 = MaxPooling2D(pool_size=(2, 2))(conv13)

    conv14 = Conv2D(16, kernel_size=3, strides=(1, 1), padding="same", activation='relu')(pool13)
    pool14 = MaxPooling2D(pool_size=(2, 2))(conv14)

    conv15 = Conv2D(convFilters[3], kernel_size=3, strides=(2, 2), activation='relu')(conv14)
    flattenOut = Flatten()(pool13)

    return flattenOut

def createConvRGB(inputCam, convFilters):
    conv11 = Conv2D(64, kernel_size=5, strides=(2, 2), activation='elu')(inputCam)
    pool11 = AveragePooling2D(pool_size=(2, 2))(conv11)
    dropout11 = Dropout(0.25)(pool11)

    conv12 = Conv2D(48, kernel_size=4, activation='relu')(dropout11)
    pool12 = AveragePooling2D(pool_size=(2, 2))(conv12)

    conv13 = Conv2D(36, kernel_size=3, strides=(2, 2), padding="same", activation='relu')(pool12)

    conv14 = Conv2D(24, kernel_size=3, activation='relu')(conv13)
    conv15 = Conv2D(16, kernel_size=3, strides=(2, 2), activation='relu')(conv14)
    flattenOut = Flatten()(conv13)

    return flattenOut


def createModel():
    convFilters = [10, 10, 10, 16, 16]

    camCentralInput = Input(shape=(144, 192, 3), name="cameraCentral")
    outCamCentral = createConv(camCentralInput, convFilters=convFilters)

    camLeftInput = Input(shape=(144, 192, 3), name="cameraLeft")
    outCamLeft = createConv(camLeftInput, convFilters=convFilters)

    camRightInput = Input(shape=(144, 192, 3), name="cameraRight")
    outCamRight = createConv(camRightInput, convFilters=convFilters)

    cameraRgbCentralInput =  Input(shape=(144, 192, 3), name="cameraRgbCentral")
    outCamRgb = createConvRGB(cameraRgbCentralInput, convFilters=convFilters)

    dataVelocity = Input(shape=1, name='dataVelocity')  # speed
    dataNav = Input(shape=4, name='dataNavigator')  # navigator
    obstacle = Input(shape=2, name='obstacle')  # obstacle
    mergeVelDataNav = concatenate([dataVelocity,dataNav, obstacle])
    outVelocityNavObs1 = Dense(64, activation='relu')(mergeVelDataNav)
    outVelocityNavObs2 = Dense(32, activation='relu')(outVelocityNavObs1)
    outVelocityNavObs3 = Dense(16, activation='relu')(outVelocityNavObs2)

    mergeAllCameras = concatenate([outCamCentral, outCamLeft, outCamRight])

    hidden1 = Dense(500,kernel_regularizer='l2', activation='relu')(mergeAllCameras)

    hidden2 = Dense(350, activation='relu')(hidden1)
    dropout2 = Dropout(0.2)(hidden2)
    hidden3 = Dense(250, activation='relu')(dropout2)
    hidden4 = Dense(120, activation='relu')(hidden3)
    hidden5 = Dense(64, activation='relu')(hidden4)
    mergeFinal = concatenate([hidden5, outVelocityNavObs3])
    hidden6 = Dense(32, activation='relu')(mergeFinal)
    output = Dense(3, activation='tanh')(hidden6)

    model = Model(inputs=[camCentralInput, camLeftInput, camRightInput,cameraRgbCentralInput, dataVelocity, dataNav, obstacle], outputs=output)

    return model


# consente di dare più importanza allo sterzo
def loss_function(y_true, y_pred):
    K1 = 4.0
    a = tf.ones([y_true.shape[0], 1], tf.float32) * K1
    paddings = tf.constant([[0, 0], [0, 2]])
    a = tf.pad(a, paddings, "CONSTANT", constant_values=1)
    y_true = tf.math.multiply(y_true, a)
    y_pred = tf.math.multiply(y_pred, a)
    return K.mean(K.square(y_pred - y_true))


def meanSteer(y_true, y_pred):
    mse = tf.keras.losses.MeanSquaredError()
    trueSteer = tf.gather(y_true, 0, axis=1)
    predSteer = tf.gather(y_pred, 0, axis=1)
    return 100*(mse(trueSteer, predSteer).numpy())

def meanThrottle(y_true, y_pred):
    mse = tf.keras.losses.MeanSquaredError()
    trueSteer = tf.gather(y_true, 1, axis=1)
    predSteer = tf.gather(y_pred, 1, axis=1)
    return 10*(mse(trueSteer, predSteer).numpy())


model = createModel()
# model = keras.models.load_model(r"D:\tesi\driveDataNew\training\test1.h5", loss_function())
print(model.summary())
plot_model(model, to_file='multiple_inputs1.png')

model.compile(loss=loss_function, optimizer=Adam(), metrics=['cosine_proximity', meanSteer], run_eagerly=True)

assert (len(cameraFiles["cameraCentral"]) == len(cameraFiles["cameraLeft"]))
assert (len(cameraFiles["cameraCentral"]) == len(cameraFiles["cameraRight"]))
assert (len(cameraFiles["cameraCentral"]) == len(x_vehicleState))
assert (len(cameraFiles["cameraCentral"]) == len(y_vehicleData))

print("Numero campioni prima della riduzione: ", len(cameraFiles["cameraCentral"]))
filesCentral, filesLeft, filesRight,cameraRGB, x_vehicleState, x_dataNav, x_obstacleSensor, y_vehicleData = reduceZerosSteer(cameraFiles["cameraCentral"],
                                                                                      cameraFiles["cameraLeft"],
                                                                                      cameraFiles["cameraRight"],
                                                                                      cameraFiles["cameraRgbCentral"],
                                                                                      x_vehicleState,
                                                                                      x_dataNav,
                                                                                      x_obstacleSensor,
                                                                                      y_vehicleData, 0.10)

print("Numero campioni validazione prima della riduzione: ", len(val_cameraFiles["cameraCentral"]))
val_filesCentral, val_filesLeft, val_filesRight,val_cameraRGB, val_x_vehicleState, val_x_dataNav, val_x_obstacleSensor, val_y_vehicleData = reduceZerosSteer(val_cameraFiles["cameraCentral"], val_cameraFiles["cameraLeft"],
                      val_cameraFiles["cameraRight"], val_cameraFiles["cameraRgbCentral"],
                      valx_vehicleState, valx_dataNav, valx_obstacleSensor, valy_vehicleData, 0.15)

assert (len(filesCentral) == len(filesLeft))
assert (len(filesCentral) == len(filesRight))
assert (len(filesCentral) == len(x_vehicleState))
assert (len(filesCentral) == len(x_dataNav))
assert (len(filesCentral) == len(y_vehicleData))
print("Numero campioni dopo la riduzione: ", len(filesCentral))
print(f"Numero campioni validazione dopo la riduzione: {len(val_filesCentral)}", )

x_dataNav = [w[0] + [w[1]] for w in x_dataNav]
val_x_dataNav = [w[0] + [w[1]] for w in val_x_dataNav]

train_gen = generator(filesCentral, filesLeft, filesRight,cameraRGB, x_vehicleState,x_dataNav,x_obstacleSensor, y_vehicleData, extract_image, BATCH_SIZE)

valid_gen = generator(val_filesCentral, val_filesLeft, val_filesRight,val_cameraRGB,
                      val_x_vehicleState, val_x_dataNav, val_x_obstacleSensor, val_y_vehicleData,
                      extract_image, BATCH_SIZE)

checkpoint = ModelCheckpoint("model.h5", monitor='val_loss', mode='min', verbose=1, save_best_only=True)
early_stopping = EarlyStopping(patience=4, verbose=1, monitor='val_loss')

if True:
    print(f"start training... steps_per_epoch={len(y_vehicleData) / BATCH_SIZE}")
    history_object = model.fit(train_gen,
                           epochs=50, steps_per_epoch=len(y_vehicleData) / BATCH_SIZE, verbose=1,
                           validation_data=valid_gen, validation_steps=len(valy_vehicleData) / BATCH_SIZE,
                           shuffle=False, callbacks=[checkpoint, early_stopping])

    print("end training...")
# else:
#     for b in valid_gen:
#         print(b)
# with open('/trainHistoryDict', 'wb') as file_pi:
#     pickle.dump(history_object.history, file_pi)

np.save('my_history3.npy',history_object.history)

history = np.load('my_history3.npy',allow_pickle='TRUE').item()