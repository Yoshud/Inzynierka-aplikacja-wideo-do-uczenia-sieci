import time
from pathlib import Path

from SimpleSMAppTracingModel import SimpleSMAppTracingModel
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.abspath(__file__), '../..')))
from internalConnection.InternalConnection import InternalConnection

url = "http://localhost:8000/learn"
urlResponse = "http://localhost:8000/learnResults"
connection = InternalConnection(url, urlResponse)


def sendingRequest(results):
    return connection.sendResponse(results)


def checkForOrderToProcess():
    json = connection.getData()
    if json:
        return json if len(json["sets"]["train_data"]) > 0 else False
    else:
        return False


def waitForLearnOrders(*args, **kwargs):
    while 1:
        data = checkForOrderToProcess()
        if (data):
            return processLearnOrder, data
        else:
            print("wait")
            time.sleep(5)
            return waitForLearnOrders, None


def processLearnOrder(data):
    learn_id = data["learn_id"]
    parameters = data["parameters"]
    model_path = data["model_path"]
    sets = data["sets"]

    model = SimpleSMAppTracingModel(**parameters)
    model.fit(**sets)
    model.save(Path(model_path))

    sendingRequest({"result": [], "learn_id": learn_id})

    return waitForLearnOrders, None


fun = waitForLearnOrders
data = None
while 1:
    fun, data = fun(data)
