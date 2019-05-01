import time
# from openCV.main import process
from openCV.processFilm import process
from internalConnection.InternalConnection import InternalConnection

url = "http://localhost:8000/returnMoviesToProcess"
urlResponse = "http://localhost:8000/movieProcessed"
connection = InternalConnection(url, urlResponse)


def sendingRequest(movieId, frames):
    payload = {
        "movieId": movieId,
        "frames": frames,
    }
    return connection.sendResponse(payload)


def checkForFilmToProcess():
    json = connection.getData()
    if json:
        return json["movies"] if len(json["movies"]) > 0 else False
    return False


def waitForMovies(data):
    while 1:
        movies = checkForFilmToProcess()
        if(movies):
            return processMovies, movies
        else:
            print("wait")
            time.sleep(10)
            return waitForMovies, None


def processMovies(data):
    for movie in data:
        print (movie["id"])
        frameInfo = process(path=movie["path"], pathToSave=movie["pathToSave"], movieName=movie["movieName"], movieId=movie["id"])
        sendingRequest(movie["id"], frameInfo)
    return waitForMovies, None


fun = waitForMovies
data = None
while 1:
    fun, data = fun(data)
