import time
import os
from openCV.dataAugmentationFunctions import process
import cv2
from pathlib import Path
from internalConnection.InternalConnection import InternalConnection

url = "http://localhost:8000/dataAugmentationOrder"
urlResponse = "http://localhost:8000/imageAfterDataAugmentation"
connection = InternalConnection(url, urlResponse)


def sendingRequest(pointPosition, cropPosition, resizeScale, frameId, imageName, methodCode, orderId, colorId):
    payload = {
        "pointPosition": list(pointPosition.astype(str)),
        "cropPosition": list(cropPosition.astype(str)),
        "resizeScale": resizeScale,
        "frameId": frameId,
        # "toImagePath": toImagePath,
        "imageName": imageName,
        "methodCode": methodCode,
        "orderId": orderId,
        "colorId": colorId
    }
    return connection.sendResponse(payload)


def checkForOrderToProcess():
    json = connection.getData()
    if json:
        return json["orders"] if len(json["orders"]) > 0 else False
    else:
        return False


def waitForOrders(data):
    while 1:
        orders = checkForOrderToProcess()
        if (orders):
            return processOrders, orders
        else:
            print("wait")
            time.sleep(5)
            return waitForOrders, None

def fileNameAndSufixFromPath(path):
    fileName = os.path.basename(path)
    fileNameAndSufix = fileName.split('.')
    fileNameWithoutSufix = '.'.join(fileNameAndSufix[:-1])
    fileSufix = fileNameAndSufix[-1]
    return fileNameWithoutSufix, fileSufix


def processOrders(data):
    for order in data:
        pathToSave = order["pathToSave"]
        pathToCreate = Path(pathToSave)
        pathToCreate.mkdir(parents=True, exist_ok=True)
        path = order["framePath"]
        frameId = order["frameId"]
        orderId = order["orderId"]
        color = order["colorName"]
        colorId = order["colorId"]
        fileName, fileSufix = fileNameAndSufixFromPath(path)

        imgs = process(path, order["pointPosition"], order["augmentationCode"])
        for imgDict in imgs:
            imgName = "{}_{}_{}_{}.{}".format(fileName, imgDict["methodCode"], id(imgs), color, fileSufix)
            fullPathToSave = os.path.join(pathToSave, imgName).replace('\\', '/')

            if cv2.imwrite(fullPathToSave, imgDict["img"], [cv2.IMWRITE_PNG_COMPRESSION, 0]):
                sendingRequest(
                    imageName=imgName,
                    frameId=frameId,
                    pointPosition=imgDict["position"],
                    cropPosition=imgDict["cropPosition"],
                    resizeScale=imgDict["resizeScale"],
                    methodCode=imgDict["orginalMethodCode"],
                    orderId=orderId,
                    colorId=colorId
                )
    return waitForOrders, None


fun = waitForOrders
data = None
while 1:
    fun, data = fun(data)
