import cv2
import datetime as time
import os
from pathlib import Path
from openCV.calculateCropPoint import *
from functools import reduce


def saveFile(path, fileName, methodTag, img, imgSufix="jpg"):
    fullPath = os.path.join(path, "{}_{}.{}".format(fileName, methodTag, imgSufix)).replace('\\', '/')
    cv2.imwrite(fullPath, img)


def flipPointPosition(position, imgShape, flipType):
    retPosition = list(position)
    positionIt = (flipType + 1) % 2  # 1 jeśli 0, 0 jeśli 1
    retPosition[positionIt] = imgShape[flipType] - retPosition[positionIt]
    return retPosition


def cropAndResizeNewPointPosition(pointPosition, cropPosition, imgShape, expectedSize, cropScale=0.8):
    expectedSize = np.array(expectedSize)
    imgHeight = imgShape[0]
    positionTowardCropCenter = -(cropPosition - pointPosition)
    positionTowardCropCenterAfterResize = expectedSize[0] / (cropScale * imgHeight) * positionTowardCropCenter
    positionTowardLeftTopCorner = expectedSize / 2 + positionTowardCropCenterAfterResize
    return positionTowardLeftTopCorner


def flipHorizontal(img, position):
    flipped = cv2.flip(img, 1)
    return flipped, flipPointPosition(position, img.shape, 1)


def flipVertical(img, position):
    flipped = cv2.flip(img, 0)
    return flipped, flipPointPosition(position, img.shape, 0)


def crop(img, height, width, x0=-1, y0=-1):
    x0 = img.shape[0] / 2 if x0 == -1 else x0
    y0 = img.shape[1] / 2 if y0 == -1 else y0

    xmin = int(x0 - height / 2)
    xmax = int(x0 + height / 2)
    ymin = int(y0 - width / 2)
    ymax = int(y0 + width / 2)

    return img[ymin:ymax, xmin:xmax]


def resize(img, size=(0, 0), scale=0):
    img = cv2.resize(img, tuple(size), scale, scale, interpolation=cv2.INTER_AREA)
    return img


def cropWithResize(img, expectedSize, cropHeight, cropWidth, x0=-1, y0=-1):
    croped = crop(img, cropHeight, cropWidth, x0=x0, y0=y0)
    return resize(croped, size=expectedSize)


def randomCrop(img, expectedSize, pointPosition, numberOfCrops):
    cropScale = 0.8
    imgHeight = img.shape[0]
    if numberOfCrops == 1:
        cropPositions = [cropPositionZero(img.shape, pointPosition, toBorderHeightFactor=0.0).astype(int), ]
    else:
        cropPositions = [randomCropPosition(img.shape, pointPosition) for it in range(numberOfCrops)]
    newPointPositions = [cropAndResizeNewPointPosition(pointPosition, cropPosition, img.shape, expectedSize)
                         for cropPosition in cropPositions]
    cropWithResizeArgs = img, expectedSize, cropScale * imgHeight, cropScale * imgHeight
    imgs = [cropWithResize(*cropWithResizeArgs, *cropPosition) for cropPosition in cropPositions]
    return imgs, newPointPositions, cropPositions


def process2(paths, pathToSave, fileNames):
    pathToCreate = Path(pathToSave)
    pathToCreate.mkdir(parents=True, exist_ok=True)
    frameInfo = []


def flipToReduce(flipMethod, methodCode, augmentationCode, imgsDict):
    if augmentationCode:
        img = imgsDict[0]["img"]
        position = imgsDict[0]["position"]
        retImg, retPosition = flipMethod(img, position)
        imgsDict.append({
            "img": retImg,
            "position": retPosition,
            "methodCode": methodCode,
        })
        return imgsDict
    else:
        return imgsDict


def resizeScale(imgHeight, expectedSize, cropScale=0.8):
    return (imgHeight * cropScale) / expectedSize[0]


def flipVerticalToReduce(augmentationCode, imgsDict):
    return flipToReduce(flipVertical, "V", augmentationCode, imgsDict)


def flipHorizontalToReduce(augmentationCode, imgsDict):
    return flipToReduce(flipHorizontal, "H", augmentationCode, imgsDict)


class RandomCropFunctor:
    def __init__(self, expectedSize):
        self.expectedSize = expectedSize

    def __call__(self, augmentationCode, imgsDict):
        retImgsDict = []
        for imgDict in imgsDict:
            img = imgDict["img"]
            position = imgDict["position"]
            methodCode = imgDict["methodCode"]
            retImgs, retPositions, retCropPositions, = randomCrop(img, self.expectedSize, position, augmentationCode)
            retResizeScale = resizeScale(img.shape[0], self.expectedSize)
            for retImg, retPosition, retCropPosition in zip(retImgs, retPositions, retCropPositions):
                retImgsDict.append({
                    "img": retImg,
                    "position": retPosition,
                    "methodCode": "{}_{}_{}_{}".format(methodCode, "crop", retCropPosition[0], retCropPosition[0]),
                    "orginalMethodCode": methodCode,
                    "resizeScale": retResizeScale,
                    "cropPosition": retCropPosition
                })
        return retImgsDict


# def randomCrop(img, expectedSize, pointPosition, numberOfCrops):
def process(path, pointPosition, augmentationCode, expectedSize):
    img = cv2.imread(path.replace('\\', '/'))
    functions = [flipVerticalToReduce, flipHorizontalToReduce, RandomCropFunctor(expectedSize)]
    imgsDict = [{
        "img": img,
        "position": pointPosition,
        "methodCode": "O",
    }, ]
    augmentationCodeStr = str(augmentationCode)[1:]
    functionsWithCode = list(zip(functions, augmentationCodeStr))
    imgs = reduce(lambda imgsDict, funCode: funCode[0](int(funCode[1]), imgsDict),
                  functionsWithCode,
                  imgsDict)
    return imgs
