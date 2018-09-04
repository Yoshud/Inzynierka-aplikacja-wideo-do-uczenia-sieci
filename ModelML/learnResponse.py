import time
import os
import requests
import json
from ModelML.simpleModel import train
from ModelML.dataBatch import Data_picker
from ModelML.optimizerMethod import optimizeMethodDict
from ModelML.lossMethod import lossMethodDict

url = "http://localhost:8000/learn"
urlResponse = "http://localhost:8000/learnResults"


def sendingRequest(results):
    r = requests.post(urlResponse, data=json.dumps(results))
    if r.json()["ok"]:
        return True
    return False


def checkForOrderToProcess():
    r = requests.get(url)
    json = r.json()
    return {
        "sets": (json["trainSet"], json["testSet"]),
        "parameters": json["parameters"],
        "learn_id": json["learn_id"],
    } if len(json["trainSet"]) > 0 else False


def waitForLearnOrders(data):
    while 1:
        data = checkForOrderToProcess()
        if (data):
            return processLearnOrder, data
        else:
            print("wait")
            time.sleep(5)
            return waitForLearnOrders, None


def objectParameters(data, object):
    objectParameters = data["parameters"]["others"][object]
    objectType = objectParameters["type"]
    try:
        objectParams = objectParameters["parameters"]
    except KeyError:
        objectParams = {}
    return objectType, objectParams


def getOptimizer(data):
    optimizerType, optimizerParams = objectParameters(data, "optimizer")
    optimizerParams["learning_rate"] = data["parameters"]["learning_rate"]

    optimizer = optimizeMethodDict[optimizerType].get(**optimizerParams)
    return optimizer


def getLoss(data):
    lossType, lossParams = objectParameters(data, "loss")
    lossMethod = lossMethodDict[lossType]
    if lossParams:
        lossMethod.set(**lossParams)
    return lossMethod.get

def getDataParameters(data):
    parameters = data["parameters"]
    for key, value in parameters["network"].items():
        parameters[key] = value
    return parameters

def processLearnOrder(data):
    data_picker = Data_picker(4, 2, 10, (320, 320), *data["sets"])
    optimizer = getOptimizer(data)
    lossMethod = getLoss(data)
    parameters = getDataParameters(data)
    learn_id = data["learn_id"]
    results = train(optimizer_type=optimizer, loss_fun=lossMethod, data_picker=data_picker, **parameters)
    sendingRequest({"result": results, "learn_id": learn_id})
    return waitForLearnOrders, None


fun = waitForLearnOrders
data = None
while 1:
    fun, data = fun(data)
