from django.shortcuts import render
from django.http import HttpResponse
import mainServer.skryptyEtapy.Etap1 as etap1
import mainServer.skryptyEtapy.Etap2 as etap2
import mainServer.skryptyEtapy.Etap3 as etap3
import mainServer.skryptyEtapy.Etap4 as etap4


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


getObjectsFromPathView = etap1.GetObjectsFromPath.as_view()
addMovieView = etap1.AddMovie.as_view()

returnMoviesToProcessView = etap2.ReturnMoviesToProcess.as_view()
movieProcessedView = etap2.MovieProcessed.as_view()
getNextMovieView = etap2.GetNextMovie.as_view()
getFrameView = etap2.GetFrame.as_view()
framePositionsView = etap2.FramePosition.as_view()
deletePositionView = etap2.DeletePosition.as_view()

dataAugmentationOrderView = etap3.DataAugmentationOrder.as_view()
imageAfterDataAugmentationView = etap3.ImageAfterDataAugmentation.as_view()
neuralNetworksView = etap3.NeuralNetworks.as_view()
parametersMethodsArgumentsView = etap3.ParametersMethodsArguments.as_view()
augmentationProcessStatusView = etap3.AugmentationProcessStatus.as_view()

divideIntoSetsView = etap4.DivideIntoSets.as_view()
learnView = etap4.Learn.as_view()
learnResultsView = etap4.LearnResults.as_view()
