from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('pathObjects', views.pathObjectsView, name='pathObjects'),
    path('movies', views.moviesView, name='movies'),
    path('processMovie', views.processMovieView, name='processMovie'),
    path('nextMovie', views.nextMovieView, name='nextMovie'),
    path('frame', views.frameView, name='frame'),
    path('framePositions', views.framePositionsView, name='framePositions'),
    path('dataAugmentationOrder', views.dataAugmentationOrderView, name='dataAugmentationOrder'),
    path('imageAfterDataAugmentation', views.imageAfterDataAugmentationView, name='imageAfterDataAugmentation'),
    path('divideIntoSets', views.divideIntoSetsView, name='divideIntoSets'),
    path('learn', views.learnView, name='learn'),
    path('neuralNetworks', views.neuralNetworksView, name='neuralNetworks'),
    path('learnResults', views.learnResultsView, name='learnResults'),
    path('parametersMethodsArguments', views.parametersMethodsArgumentsView, name='parametersMethodsArguments'),
    path('augmentationProcessStatus', views.augmentationProcessStatusView, name='augmentationProcessStatus'),
]
