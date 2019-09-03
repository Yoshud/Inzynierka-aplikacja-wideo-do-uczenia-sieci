from django.http import HttpResponse
import mainServer.stages.stage_1 as stage_1
import mainServer.stages.stage_2 as stage_2
import mainServer.stages.stage_3
import mainServer.stages.stage_3 as stage_3
import mainServer.stages.stage_4
import mainServer.stages.stage_4 as stage_4


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


getObjectsFromPathView = stage_1.GetObjectsFromPath.as_view()
addMovieView = stage_1.AddMovie.as_view()

processMovieView = stage_2.ProcessMovie.as_view()
getNextMovieView = stage_2.GetNextMovie.as_view()
getFrameView = stage_2.GetFrame.as_view()
framePositionsView = stage_2.FramePosition.as_view()
deletePositionView = stage_2.DeletePosition.as_view()

dataAugmentationOrderView = stage_3.DataAugmentationOrder.as_view()
imageAfterDataAugmentationView = stage_3.ImageAfterDataAugmentation.as_view()
neuralNetworksView = mainServer.stages.stage_4.NeuralNetworks.as_view()
parametersMethodsArgumentsView = mainServer.stages.stage_4.ParametersMethodsArguments.as_view()
augmentationProcessStatusView = stage_3.AugmentationProcessStatus.as_view()

divideIntoSetsView = mainServer.stages.stage_3.DivideIntoSets.as_view()
learnView = stage_4.Learn.as_view()
learnResultsView = stage_4.LearnResults.as_view()
