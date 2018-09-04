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
            raise Http404
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
class AddMovie(View):
    def get(self, request, **kwargs):
        path = request.GET.get('path', '')
        cap = cv2.VideoCapture(path)
        if cap is None or not cap.isOpened():
            raise Http404
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

    def post(self, request, **kwargs):
        data = json.loads(request.read().decode('utf-8'))
        path = data.get('path', '')
        if path == '':
            raise Http404
        files = data.get('files')
        folders = data.get('folders')
        sessionName = data.get('sessionName', 'autoName')
        now = timezone.now()
        sessionName = "{}_{}_{}".format(sessionName, now.date(), now.time()).replace(":", "_").replace(".", "_")
        sessionPath = data.get('toFolderPath', '')
        sessionPath = os.path.join(os.path.join(pathUp(currentPath()), 'Sesje'), sessionName) \
            if sessionPath == '' else sessionPath
        imagesPath = os.path.join(sessionPath, 'Obrazy')
        modelsPath = os.path.join(sessionPath, 'Modele')
        processedPath = os.path.join(sessionPath, 'Przygotowane')

        imageFolder = FolderZObrazami(sciezka=imagesPath)
        imageFolder.save()
        modelsFolder = FolderModele.objects.create(sciezka=modelsPath)
        processedFolder = FoldeZPrzetworzonymiObrazami.objects.create(sciezka=processedPath)

        session = Sesja(
            nazwa=sessionName,
            folderZObrazami=imageFolder,
            folderModele=modelsFolder,
            folderPrzetworzone=processedFolder
        )
        session.save()
        request.session["sessionPk"] = session.pk
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
        statuses = [StatusFilmu.objects.get_or_create(status=tag)[0] for tag in statusTags]
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
