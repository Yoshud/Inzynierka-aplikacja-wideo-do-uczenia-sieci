import cv2
import os
from calculateCropPoint import *
from functools import reduce


def saveFile(path, fileName, methodTag, img, imgSufix="jpg"):
    fullPath = os.path.join(path, "{}_{}.{}".format(fileName, methodTag, imgSufix)).replace('\\', '/')
    cv2.imwrite(fullPath, img)


def flipPointPosition(position, imgShape, flipType):
    if position is not None:
        retPosition = list(position)
        positionIt = (flipType + 1) % 2
        retPosition[positionIt] = imgShape[flipType] - retPosition[positionIt]
        return retPosition
    else:
        return None


def flipHorizontal(img, positions):
    flipped = cv2.flip(img, 1)
    newPositions = [flipPointPosition(position, img.shape, 1) for position in positions.values()]
    return flipped, dict(zip(positions.keys(), newPositions))


def flipVertical(img, positions):
    flipped = cv2.flip(img, 0)
    newPositions = [flipPointPosition(position, img.shape, 0) for position in positions.values()]
    return flipped, dict(zip(positions.keys(), newPositions))


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
        positions = imgsDict[0]["positions"]

        retImg, retPositions = flipMethod(orginalImg, positions)
        imgsDict.append({
            "img": retImg,
            "positions": retPositions,
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
            positions = imgDict["positions"]
            methodCode = imgDict["methodCode"]
            retImgs, retPositionss, retCropPositions, = randomCrop(img, positions.values(), augmentationCode)
            for retImg, retPositions, retCropPosition in zip(retImgs, retPositionss, retCropPositions):
                retImgsDict.append({
                    "img": retImg,
                    "positions": dict(zip(positions.keys(), retPositions)),
                    "methodCode": "{}_{}_{}_{}".format(methodCode, "crop", retCropPosition[0], retCropPosition[1]),
                    "orginalMethodCode": methodCode,
                    "cropPosition": retCropPosition
                })
        return retImgsDict


def process(path, pointPositions, augmentationCode):
    img = cv2.imread(path.replace('\\', '/'))
    functions = [flipVerticalToReduce, flipHorizontalToReduce, RandomCropFunctor()]
    imgsDict = [{
        "img": img,
        "positions": pointPositions,
        "methodCode": "O",
    }, ]
    augmentationCodeStr = str(augmentationCode)[1:]
    functionsWithCode = list(zip(functions, augmentationCodeStr))
    imgs = reduce(lambda imgsDict, funCode: funCode[0](int(funCode[1]), imgsDict),
                  functionsWithCode,
                  imgsDict)
    return imgs

#TODO: przerobić do działania z wieloma punktami na raz oraz z punktem typu None, zmodyfikować wtedy wstęp tak by sprawdzał braki punktu i dawał w sposób odpowiedni DONE
# zmodyfikować tak by pozycji było podawane jako JSON ( kolor: kolor, pozycja: pozycja (brak pozycji gdy Brak punktu ) DONE
# zmodyfikowac divideIntoSets itp. z Etapu4 do odpowiedniego dzialania
# zmodyfikować machineLearning dodając kolejną funkcje jako oddzielny skrypt która tłumaczy te punkty na odpowiednie modele
# funkcje te zrobić jako klasę którą się pickluje i dodać by zapisywało się wszystko w jakimś folderze tab by tą klasę się odpicklowywało
# dawalo load i by mozna już jej uzywać z jakims predict
# nastepnie wytrenowac model i zrobić pokaz
# potem mozna bedzie dodawac kolejne modele poprzez odpowiednie ich tworzenie tak by ten interfejs utrzymywaly
# nastepny model bedzie z pytorchem z odpowiednim pyTorchowym dataLoaderem