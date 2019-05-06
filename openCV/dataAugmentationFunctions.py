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
    positionIt = (flipType + 1) % 2
    retPosition[positionIt] = imgShape[flipType] - retPosition[positionIt]
    return retPosition


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


def randomCrop(img, pointPosition, numberOfCrops):
    imgHeight = img.shape[0]
    cropPositions, pointPositions = zip(*[randomCropPosition(img.shape, pointPosition) for it in range(numberOfCrops)])

    cropArgs = img, imgHeight, imgHeight
    imgs = [crop(*cropArgs, *cropPosition) for cropPosition in cropPositions]
    return imgs, pointPositions, cropPositions


def flipToReduce(flipMethod, methodCode, augmentationCode, imgsDict):
    if augmentationCode:
        orginalImg = imgsDict[0]["img"]
        position = imgsDict[0]["position"]

        retImg, retPosition = flipMethod(orginalImg, position)
        imgsDict.append({
            "img": retImg,
            "position": retPosition,
            "methodCode": methodCode,
        })

    return imgsDict


def flipVerticalToReduce(augmentationCode, imgsDict):
    return flipToReduce(flipVertical, "V", augmentationCode, imgsDict)


def flipHorizontalToReduce(augmentationCode, imgsDict):
    return flipToReduce(flipHorizontal, "H", augmentationCode, imgsDict)


class RandomCropFunctor:
    def __call__(self, augmentationCode, imgsDict):
        retImgsDict = []
        for imgDict in imgsDict:
            img = imgDict["img"]
            position = imgDict["position"]
            methodCode = imgDict["methodCode"]
            retImgs, retPositions, retCropPositions, = randomCrop(img, position, augmentationCode)
            for retImg, retPosition, retCropPosition in zip(retImgs, retPositions, retCropPositions):
                retImgsDict.append({
                    "img": retImg,
                    "position": retPosition,
                    "methodCode": "{}_{}_{}_{}".format(methodCode, "crop", retCropPosition[0], retCropPosition[0]),
                    "orginalMethodCode": methodCode,
                    "resizeScale": 1,
                    "cropPosition": retCropPosition
                })
        return retImgsDict


def process(path, pointPosition, augmentationCode):
    img = cv2.imread(path.replace('\\', '/'))
    functions = [flipVerticalToReduce, flipHorizontalToReduce, RandomCropFunctor()]
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
