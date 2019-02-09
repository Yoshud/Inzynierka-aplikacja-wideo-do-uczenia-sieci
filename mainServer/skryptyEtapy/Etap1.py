from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from mainServer.skryptyEtapy.helpersMethod import *
import cv2
import datetime
from mainServer.models import *
from django.utils import timezone
import json


@method_decorator(csrf_exempt, name='dispatch')
class GetObjectsFromPath(View):
    def get(self, request, **kwargs):
        path = request.GET.get('path', None)
        parent = request.GET.get('parent', None)
        child = request.GET.get('child', '')
        if path == None:
            raise HttpResponseBadRequest
        if parent != None:
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
class AddMovie(JsonView):
    def get_method(self):
        path = self._get_data('path')
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
        path = self._get_data_or_error("path")
        files = self._get_data("files")
        folders = self._get_data('folders')
        sessionName = self._get_data('sessionName', 'autoName')
        now = timezone.now()

        sessionName = "{}_{}_{}".format(sessionName, now.date(), now.time()).replace(":", "_").replace(".", "_")
        sessionPath = \
            self._get_data('toFolderPath', os.path.join(os.path.join(pathUp(currentPath()), 'Sesje'), sessionName))

        imageFolder = FolderZObrazami.objects.create(nazwa=imagesFolderName)
        modelsFolder = FolderModele.objects.create(nazwa=modelsFolderName)
        processedFolder = FoldeZPrzetworzonymiObrazami.objects.create(nazwa=processedFolderName)

        session = Sesja(
            nazwa=sessionName,
            sciezka=sessionPath,
            folderZObrazami=imageFolder,
            folderModele=modelsFolder,
            folderPrzetworzone=processedFolder
        )
        session.save()
        if files:
            for file in files:
                self.addMovie(session.pk, os.path.join(path, file))
        if folders:
            for folder in folders:
                self.addFolder(session.pk, os.path.join(path, folder))
        return JsonResponse({
            'sessionId': session.pk
        })

    def addMovie(self, sessionPK, path):
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
            sesja=Sesja.objects.get(pk=sessionPK),
        )
        film.save()
        for status in statuses:
            film.status.add(status)

    def addFolder(self, sessionPK, path):
        folders, files = foldersAndMovieFilesFromPath(path)
        for file in files:
            self.addMovie(sessionPK, os.path.join(path, file))
