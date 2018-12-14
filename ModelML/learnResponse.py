import time
from ModelML.simpleModelKeras import train
from ModelML.dataBatchKeras import Data_picker
from ModelML.optimizerMethod import optimizeMethodDict
from ModelML.lossMethod import lossMethodDict
from internalConnection.InternalConnection import InternalConnection

url = "http://localhost:8000/learn"
urlResponse = "http://localhost:8000/learnResults"
connection = InternalConnection(url, urlResponse)

def sendingRequest(results):
    return connection.sendResponse(results)


def checkForOrderToProcess():
    json = connection.getData()
    if json:
        return {
            "sets": (json["trainSet"], json["testSet"]),
            "parameters": json["parameters"],
            "learn_id": json["learn_id"],
        } if len(json["trainSet"]) > 0 else False
    else:
        return False


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
    parameters = getDataParameters(data)
    learn_id = data["learn_id"]

    data_picker = Data_picker(
        parameters["batch_size"], parameters["epoch_size"], parameters["training_iters"],
        (parameters["img_size_x"], parameters["img_size_y"]), *data["sets"]
    )

    optimizer = getOptimizer(data)
    lossMethod = getLoss(data)

    results = train(optimizer_type=optimizer, loss_fun=lossMethod, data_picker=data_picker, **parameters)
    sendingRequest({"result": results, "learn_id": learn_id})

    return waitForLearnOrders, None


fun = waitForLearnOrders
data = None
while 1:
    fun, data = fun(data)
