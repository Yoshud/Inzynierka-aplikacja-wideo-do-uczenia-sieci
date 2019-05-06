import numpy as np


def imageCenter(imgShape):
    imgSize = np.array(imgShape[1::-1])
    imgCenter = imgSize / 2
    return imgCenter


def randomDeltaFromPosition0(imgShape, moveHeightFactor):
    imgHeight = imgShape[0]
    maxDistanceiInPx = moveHeightFactor * imgHeight
    randValue = 2 * (np.random.rand(1) - 0.5)
    deltaRand = np.array([randValue * maxDistanceiInPx, 0])
    return deltaRand.astype(int)


def randomCropPosition(imgShape, pointPosition, moveHeightFactor=0.1):
    imgHeight = imgShape[0]
    randomDelta = randomDeltaFromPosition0(imgShape, moveHeightFactor)
    cropPosition = imageCenter(imgShape) + randomDelta

    newPointPosition = imageCenter([imgHeight, imgHeight]) - (cropPosition - pointPosition)
    normalizedNewPointPosition = newPointPosition / imgHeight

    return cropPosition, normalizedNewPointPosition
