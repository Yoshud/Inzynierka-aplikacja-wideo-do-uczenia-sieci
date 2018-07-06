from django.shortcuts import render
from django.http import HttpResponse
import mainServer.skryptyEtapy.Etap1 as etap1

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

getObjectsFromPathView = etap1.GetObjectsFromPath.as_view()
addMovieView = etap1.AddMovie.as_view()