from django.http import JsonResponse, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponseBadRequest

from mainServer.stages.JsonView import JsonView
from mainServer.stages.auxiliaryMethods import *
import cv2
import datetime
from mainServer.models import *
from django.utils import timezone
import re
import shutil


@method_decorator(csrf_exempt, name='dispatch')
class PathObjects(JsonView):
    def get_method(self):
        path = self.get_data_or_error('path')
        parent = self.get_data('parent', allow_empty_value=True)
        child = self.get_data('child', '')

        if parent is not None:
            path = pathUp(path)
        else:
            if child != '':
                path = os.path.join(path, child)
        folders, files = foldersAndMovieFilesFromPath(path)
        return JsonResponse({
            "currentDir": path,
            "folders": folders,
            "files": files,
        })


@method_decorator(csrf_exempt, name='dispatch')
class Movies(JsonView):
    def get_method(self):
        path = self.get_data_or_error('path')
        cap = cv2.VideoCapture(path)
        if cap is None or not cap.isOpened():
            return HttpResponseBadRequest()

        fps = cap.get(cv2.CAP_PROP_FPS)
        iloscKlatek = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        dlugosc = iloscKlatek / fps
        dlugosc = datetime.timedelta(seconds=dlugosc)
        x = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        y = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        return JsonResponse({
            "fps": fps,
            "iloscKlatek": int(iloscKlatek),
            "dlugosc": str(dlugosc),
            "x": int(x),
            "y": int(y),
        })

    def post_method(self):
        path = self.get_data_or_error("path")
        files = self.get_data("files")
        folders = self.get_data('folders')

        sessionId = self.get_data("sessionId")
        if sessionId is None:
            sessionName = self.get_data('sessionName', 'autoName')
            now = timezone.now()

            sessionName = "{}_{}_{}".format(sessionName, now.date(), now.time()).replace(":", "_").replace(".", "_")
            sessionPath = self.get_data('sessionPath', os.path.join(pathUp(currentPath()), 'Sesje'))
            sessionPath = os.path.join(sessionPath, sessionName)

            imageFolder = FolderZObrazami.objects.create(nazwa=imagesFolderName)
            modelsFolder = FolderModele.objects.create(nazwa=modelsFolderName)
            processedFolder = FoldeZPrzetworzonymiObrazami.objects.create(nazwa=processedFolderName)

            session = Sesja(
                nazwa=sessionName,
                sciezka=sessionPath,
                folderZObrazami=imageFolder,
                folderModele=modelsFolder,
                folderPrzetworzone=processedFolder,
                zbiorKolorow_id=ZbiorKolorow.objects.get(nazwa="Domyslny zestaw").pk
            )
            session.save()
        else:
            session = Sesja.objects.get(pk=sessionId)

        if files:
            for file in files:
                self._addMovie(session.pk, os.path.join(path, file))
        if folders:
            for folder in folders:
                self._addFolder(session.pk, os.path.join(path, folder))
        return JsonResponse({
            'sessionId': session.pk
        })

    @staticmethod
    def _addMovie(sessionPK, path):
        cap = cv2.VideoCapture(path)
        if cap is None or not cap.isOpened():
            raise Http404
        fps = cap.get(cv2.CAP_PROP_FPS)
        iloscKlatek = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        dlugosc = iloscKlatek / fps
        dlugosc = datetime.timedelta(seconds=dlugosc)
        x = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        y = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

        statusTags = ["Do przetworzenia", "Aktywny"]
        statuses = [StatusFilmu.objects.get(status=tag) for tag in statusTags]
        film = Film(
            sciezka=path,
            nazwa=os.path.basename(path),
            FPS=fps,
            iloscKlatek=int(iloscKlatek),
            rozmiarX=int(x),
            rozmiarY=int(y),
            dlugosc=str(dlugosc),
            sesja_id=sessionPK,
        )
        film.save()
        for status in statuses:
            film.status.add(status)

    @staticmethod
    def _getSufixNumberFromFilename(fileName):
        match = re.search(r"([0-9]+)\.(png)|(jpg)$", fileName)
        if not match:
            raise Http404
        return int(match[1])

    @classmethod
    def _groupImagesInMovies(cls, imageFileNames):
        imageFileNames.sort(key=cls._getSufixNumberFromFilename)

        movies = []
        movies.append([imageFileNames[0]])
        number = cls._getSufixNumberFromFilename(imageFileNames[0])
        for fileName in imageFileNames[1:]:
            nextImgNum = cls._getSufixNumberFromFilename(fileName)

            if nextImgNum == number + 1:
                movies[-1].append(fileName)
            else:
                movies.append([fileName])

            number = nextImgNum

        return movies

    @classmethod
    def _addMovieFromImageGroup(cls, images: list, mainPath: str, sessionPK: int) -> None:
        firstImage = cv2.imread(os.path.join(mainPath, images[0]))
        y, x, z = firstImage.shape
        session = Sesja.objects.get(pk=sessionPK)
        pathToSaveImages = session.folderZObrazami.getPath()
        movieName = os.path.basename(mainPath)

        createDirPath(pathToSaveImages)
        movie = Film.objects.create(
            sciezka=mainPath,
            nazwa=movieName,
            iloscKlatek=len(images),
            rozmiarX=x,
            rozmiarY=y,
            sesja_id=sessionPK,
        )

        for i, imageName in enumerate(images):
            newImageName = f"{movieName}_{imageName}"
            shutil.copyfile(os.path.join(mainPath, imageName), os.path.join(pathToSaveImages, newImageName))
            Klatka.objects.create(nazwa=newImageName, nr=i, film=movie)

        statusTags = ["Przetworzono", "Aktywny"]
        statuses = [StatusFilmu.objects.get(status=tag) for tag in statusTags]
        for status in statuses:
            movie.status.add(status)

    @classmethod
    def _addMoviesFromImages(cls, imageFileNames, mainPath, sessionPK):
        imagesGroups = cls._groupImagesInMovies(imageFileNames)
        for imagesGroup in imagesGroups:
            cls._addMovieFromImageGroup(imagesGroup, mainPath, sessionPK)

    @classmethod
    def _addFolder(cls, sessionPK, path):
        folders, files = foldersAndMovieFilesFromPath(path)
        for file in files:
            cls._addMovie(sessionPK, os.path.join(path, file))

        cls._addMoviesFromImages(*imagesFileNamesFromPath(path), sessionPK)


# internal
@method_decorator(csrf_exempt, name='dispatch')
class ProcessMovie(JsonView):
    def post_method(self):
        movieId = self.get_data("movieId", False)
        frames = self.get_data("frames")
        try:
            self._addToProcessedMovies(Film.objects.get(pk=movieId), frames)
        except:
            raise HttpResponseServerError
        return JsonResponse({"ok": True})

    def get_method(self):
        movies = Film.objects \
                     .filter(status__status__in=["Do przetworzenia"])[:5]
        moviesDict = [self._addMovieToMoviesDict(movie) for movie in movies]
        return JsonResponse({
            "movies": moviesDict,
        })

    @staticmethod
    def _addToProcessedMovies(movie, frames,
                              statusToRemove=StatusFilmu.objects.get(status="W trakcie przetwarzania"),
                              statusToAdd=StatusFilmu.objects.get(status="Przetworzono")):
        movie.status.remove(statusToRemove)
        movie.status.add(statusToAdd)
        for frameInfo in frames:
            Klatka.objects.update_or_create(nazwa=frameInfo["name"], nr=frameInfo["nr"], film=movie,
                                            defaults=dict(nazwa=frameInfo["name"], nr=frameInfo["nr"]))

        print(movie.nazwa)

    @staticmethod
    def _addMovieToMoviesDict(movie,
                              statusToRemove=StatusFilmu.objects.get(status="Do przetworzenia"),
                              statusToAdd=StatusFilmu.objects.get(status="W trakcie przetwarzania")):
        movie.status.remove(statusToRemove)
        movie.status.add(statusToAdd)
        return {
            "path": movie.sciezka,
            "movieName": movie.nazwa,
            "id": movie.pk,
            "pathToSave": movie.sesja.folderZObrazami.getPath(),
        }
