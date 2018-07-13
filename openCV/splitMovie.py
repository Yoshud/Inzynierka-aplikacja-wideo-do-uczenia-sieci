import cv2
import time
import schedule
import os
import requests
# from openCV.main import process
from openCV.processFilm import process

url = "http://localhost:8000/returnMoviesToProcess"
urlResponse = "http://localhost:8000/movieProcessed"


def sendingRequest(id):
    payload = {
        "movieId": id
    }
    r = requests.post(urlResponse, data=payload)
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
        process(path=movie["path"], pathToSave=movie["pathToSave"], movieName=movie["movieName"] , movieId=movie["id"])
        sendingRequest(movie["id"])
    return waitForMovies, None


fun = waitForMovies
data = None
while 1:
    fun, data = fun(data)
