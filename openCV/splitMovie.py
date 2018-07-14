import time
import os
import requests
# from openCV.main import process
from openCV.processFilm import process
import json

url = "http://localhost:8000/returnMoviesToProcess"
urlResponse = "http://localhost:8000/movieProcessed"


def sendingRequest(movieId, frames):
    payload = {
        "movieId": movieId,
        "frames": frames,
    }
    r = requests.post(urlResponse, data=json.dumps(payload))
    if r.json()["ok"]:
        return True
    return False

def checkForFilmToProcess():
    r = requests.post(url)
    json = r.json()
    return json["movies"] if len(json["movies"]) > 0 else False

def waitForMovies(data):
    while 1:
        movies = checkForFilmToProcess()
        if(movies):
            return processMovies, movies
        else:
            print("wait")
            time.sleep(5)
            return waitForMovies, None


def processMovies(data):
    for movie in data:
        print (movie["id"])
        frameInfo = process(path=movie["path"], pathToSave=movie["pathToSave"], movieName=movie["movieName"] , movieId=movie["id"])
        sendingRequest(movie["id"], frameInfo)
    return waitForMovies, None


fun = waitForMovies
data = None
while 1:
    fun, data = fun(data)
