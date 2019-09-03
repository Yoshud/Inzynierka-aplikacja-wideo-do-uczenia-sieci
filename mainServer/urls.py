from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('getObjectsFromPath', views.getObjectsFromPathView, name='getObjectsFromPath'),
    path('addMovie', views.addMovieView, name='addMovie'),
    path('processMovie', views.processMovieView, name='processMovie'),
    path('getNextMovie', views.getNextMovieView, name='getNextMovie'),
    path('getFrame', views.getFrameView, name='getFrame'),
    path('framePositions', views.framePositionsView, name='framePositions'),
    path('deletePosition', views.deletePositionView, name='deletePosition'),
    path('dataAugmentationOrder', views.dataAugmentationOrderView, name='dataAugmentationOrder'),
    path('imageAfterDataAugmentation', views.imageAfterDataAugmentationView, name='imageAfterDataAugmentation'),
    path('divideIntoSets', views.divideIntoSetsView, name='divideIntoSets'),
    path('learn', views.learnView, name='learn'),
    path('neuralNetworks', views.neuralNetworksView, name='neuralNetworks'),
    path('learnResults', views.learnResultsView, name='learnResults'),
    path('parametersMethodsArguments', views.parametersMethodsArgumentsView, name='parametersMethodsArguments'),
    path('augmentationProcessStatus', views.augmentationProcessStatusView, name='augmentationProcessStatus'),
]
