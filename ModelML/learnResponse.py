import time
import os
import requests
import json
from ModelML.dataBatch import Data_picker

url = "http://localhost:8000/learn"



def sendingRequest():
    pass

def checkForOrderToProcess():
    r = requests.get(url)
    json = r.json()
    return json["trainSet"], json["testSet"] if len(json["trainSet"]) > 0 else False

def waitForLearnOrders(data):
    while 1:
        data = checkForOrderToProcess()
        if(data):
            return processLearnOrder, data
        else:
            print("wait")
            time.sleep(5)
            return waitForLearnOrders, None


def processLearnOrder(data):
    data_picker = Data_picker(4, 2, 10, (320, 320), *data)
    d = data_picker.data_batch(0)
    d1 = data_picker.data_batch(1)
    d2 = data_picker.data_batch(2)
    d3 = data_picker.data_batch(3)
    sendingRequest()
    return waitForLearnOrders, None


fun = waitForLearnOrders
data = None
while 1:
    fun, data = fun(data)
