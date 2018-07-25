import cv2
import datetime as time
import os
from pathlib import Path
from openCV.calculateCropPoint import *


def saveFile(path, fileName, methodTag, img, imgSufix="jpg"):
    fullPath = os.path.join(path, "{}_{}.{}".format(fileName, methodTag, imgSufix)).replace('\\', '/')
    cv2.imwrite(fullPath, img)


def flipPointPosition(position, imgShape, flipType):
    return imgShape[flipType] - position[flipType]


def cropAndResizeNewPointPosition(pointPosition, cropPosition, imgShape, expectedSize, cropScale=0.8):
    imgHeight = imgShape[0]
    # imgSize = np.array(imgShape[1::-1])
    positionTowardCropCenter = cropPosition - pointPosition
    positionTowardCropCenterAfterResize = expectedSize[0] / (cropScale * imgHeight) * positionTowardCropCenter
    positionTowardLeftTopCorner = expectedSize / 2 + positionTowardCropCenterAfterResize
    return positionTowardLeftTopCorner


# def flipHorizontal(img, position, path, fileNameWithoutSufix):
def flipHorizontal(img, position):
    flipped = img.flip(img, 1)
    return flipped, flipPointPosition(position, img.shape, 1)
    # saveFile(path, fileNameWithoutSufix, 'flipH', fliped)


# def flipVertical(img, position, path, fileNameWithoutSufix):
def flipVertical(img, position):
    flipped = img.flip(img, 0)
    return flipped, flipPointPosition(position, img.shape, 0)
    # saveFile(path, fileNameWithoutSufix, 'flipV', fliped)


def crop(img, height, width, x0=-1, y0=-1):
    x0 = img.shape[0] / 2 if x0 == -1 else x0
    y0 = img.shape[1] / 2 if y0 == -1 else y0

    xmin = x0 - height / 2
    xmax = x0 + height / 2
    ymin = y0 - width / 2
    ymax = y0 + width / 2

    return img[xmin:xmax, ymin:ymax]


def resize(img, size=(0, 0), scale=0):
    return cv2.resize(img, size, scale, scale, interpolation=cv2.INTER_AREA)


def cropWithResize(img, expectedSize, cropHeight, cropWidth, x0=-1, y0=-1):
    croped = crop(img, cropHeight, cropWidth, x0=-1, y0=-1)
    return resize(croped, size=expectedSize)


def randomCrop(img, expectedSize, pointPosition, numberOfCrops):
    cropScale = 0.8
    imgHeight = img.shape[0]
    if numberOfCrops == 1:
        cropPositions = [cropPositionZero(img.shape, pointPosition, toBorderHeightFactor=0.0), ]
    else:
        cropPositions = [randomCropPosition(img.shape, pointPosition) for it in range(numberOfCrops)]
    newPointPositions = [cropAndResizeNewPointPosition(pointPosition, cropPosition, img.shape, expectedSize)
                         for cropPosition in cropPositions]
    cropWithResizeArgs = img, expectedSize, cropScale * imgHeight, cropScale * imgHeight
    imgs = [cropWithResize(*cropWithResizeArgs, *cropPosition) for cropPosition in cropPositions]
    return zip(imgs, newPointPositions)


def process2(paths, pathToSave, fileNames):
    #zwraca: frameId, wsp_crop, pozycjaCrop, pozycjaPunkt
    #otrzymuje sciezke do obrazu, sciezke do zapisu, pozycje punktu, kod augmentacji, ma utworzyc nazwe i zapisac
    #reduce: zzipowane(funkcja, kodAugmentacji), retImgs(img, kodMetody, wspCrop, pozycjaCrop, pozycjaPunkt)
    #retImgs - tablica dict
    pathToCreate = Path(pathToSave)
    pathToCreate.mkdir(parents=True, exist_ok=True)
    frameInfo = []

def process(path, fileName, pathToSave, pointPosition, augmentationCode):
    functions = []
    pass

def processImg(path, fileName, pathToSave):
    fileNameAndSufix = fileName.split('.')
    fileNameWithoutSufix = '.'.join(fileNameAndSufix[:-1])
    fileSufix = fileNameAndSufix[-1]
    imageSufix = "jpg"

    # pathToSave = os.path.join(pathToSave, fileNameWithoutSufix).replace('\\', '/')
    # cap = cv2.VideoCapture(path.replace('\\', '/'))
    # fps = cap.get(cv2.CAP_PROP_FPS)
    # print("fps: {}".format(fps))
    # it = 0
    # frameTimeOld = 0
    # while 1:
    #     ret, frame = cap.read()
    #     frameTime = cap.get(cv2.CAP_PROP_POS_MSEC)
    #     delta = frameTime - frameTimeOld
    #     frameTimeOld = frameTime
    #     # print(delta)
    #     if ret != False:
    #         fullPathToSave = "{}_f{}.{}".format(pathToSave, it, imageSufix)
    #         try:
    #             cv2.imwrite(fullPathToSave, frame)
    #             frameInfo.append({
    #                 "nr": it,
    #                 "path": fullPathToSave,
    #             })
    #         except:
    #             print("??")
    #
    #         it += 1
    #     else:
    #         break
    #     if cv2.waitKey(1) & 0xFF == ord('q'):
    #         break
    #
    # cap.release()
    # cv2.destroyAllWindows()
    # return frameInfo
