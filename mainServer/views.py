from django.http import HttpResponse

import mainServer.stages.stage_1
import mainServer.stages.stage_1 as stage_1
import mainServer.stages.stage_2 as stage_2
import mainServer.stages.stage_3
import mainServer.stages.stage_3 as stage_3
import mainServer.stages.stage_4
import mainServer.stages.stage_4 as stage_4


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


pathObjectsView = stage_1.PathObjects.as_view()
moviesView = stage_1.Movies.as_view()
processMovieView = mainServer.stages.stage_1.ProcessMovie.as_view()

nextMovieView = stage_2.NextMovie.as_view()
frameView = stage_2.Frame.as_view()
framePositionsView = stage_2.FramePosition.as_view()

dataAugmentationOrderView = stage_3.DataAugmentationOrder.as_view()
imageAfterDataAugmentationView = stage_3.ImageAfterDataAugmentation.as_view()
augmentationProcessStatusView = stage_3.AugmentationProcessStatus.as_view()
divideIntoSetsView = mainServer.stages.stage_3.DivideIntoSets.as_view()

neuralNetworksView = mainServer.stages.stage_4.NeuralNetworks.as_view()
parametersMethodsArgumentsView = mainServer.stages.stage_4.ParametersMethodsArguments.as_view()
learnView = stage_4.Learn.as_view()
learnResultsView = stage_4.LearnResults.as_view()
