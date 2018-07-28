import numpy as np
import cv2

class CompareToCenter:
    def __init__(self, imgHeight, cropScale = 0.8, toMoveFactor = 0.8):
        self.xMax = cropScale*toMoveFactor*imgHeight/2

    def _compareOne(self, x):
        if x > self.xMax:
            return 1
        if x < -self.xMax:
            return -1
        return 0

    def compare(self, point):
        return [self._compareOne(x) for x in point]


def cropPositionZero(imgShape, pointPosition, cropScale = 0.8, toMoveFactor = 0.8, toBorderHeightFactor = 0.1):
    imgHeight = imgShape[0]
    compare = CompareToCenter(imgHeight, cropScale, toMoveFactor).compare

    imgSize = np.array(imgShape[1::-1])
    imgCenter = imgSize/2
    pointPosition = np.array(pointPosition)

    delta = -(imgCenter - pointPosition)
    moveVect = np.array(imgCenter - (toBorderHeightFactor + cropScale)*(imgHeight/2))
    return imgCenter + compare(delta) * moveVect

def randomCropPositionFromPosition0(position0, imgShape, toBorderHeightFactor = 0.1):
    imgHeight = imgShape[0]
    maxDistanceiInPx = toBorderHeightFactor * (imgHeight / 2)
    randFromMinusOneToOne = 2*(np.random.rand(2) - 0.5)
    deltaRand = randFromMinusOneToOne * maxDistanceiInPx
    cropPosition = position0 + deltaRand
    return cropPosition.astype(int)

def randomCropPosition(imgShape, pointPosition, cropScale = 0.8, toMoveFactor = 0.8, toBorderHeightFactor = 0.1):
    position0 = cropPositionZero(imgShape, pointPosition, cropScale, toMoveFactor, toBorderHeightFactor)
    return randomCropPositionFromPosition0(position0, imgShape, toBorderHeightFactor)

# img = cv2.imread('klatka.jpg')
# positionZero = cropPositionZero(img.shape, pointPosition=(100,24))
# a = randomCropPositionFromPosition0(positionZero, img.shape)
# a