import time
import requests
import json
from requests.exceptions import ConnectionError

class InternalConnection:
    def __init__(self, url, urlResponse):
        self._urlResponse = urlResponse
        self._url = url

    def sendResponse(self, payload):
        try:
            r = requests.post(self._urlResponse, data=json.dumps(payload))
            if r.status_code==200 and r.json()["ok"]:
                return True
            else:
                time.sleep(5)
                return self.sendResponse(payload)

        except ConnectionError:
            print("Sending Connection Error")
            time.sleep(5)
            self.sendResponse(payload)

    def getData(self):
        try:
            r = requests.get(self._url)
            if r.status_code == 200:
                json = r.json()
                return json
            else:
                return None
        except ConnectionError:
            print("no connection")
            return None