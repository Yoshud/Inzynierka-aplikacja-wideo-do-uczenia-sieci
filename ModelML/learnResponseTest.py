import time
from pathlib import Path
import json

from SimpleSMAppTracingModel import SimpleSMAppTracingModel


def checkForOrderToProcess():
    with open("response.json", "r") as file:
        jsonData = json.loads(file.read())
        if jsonData:
            return jsonData if len(jsonData["sets"]["train_data"]) > 0 else False
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

    result = {"result": [], "learn_id": learn_id}

    return waitForLearnOrders, None


fun = waitForLearnOrders
data = None

fun, data = fun(data)
fun, data = fun(data)
