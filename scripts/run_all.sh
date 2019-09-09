#!/bin/bash
cd "$(dirname "$0")/.."

nohup python3 manage.py runserver &
export SPLIT_MOVIE_MAIN_SERVER_PID=$!

nohup python3 openCV/splitMovie.py &
export SPLIT_MOVIE_SPLIT_MOVIE_SERVICE_PID=$!

nohup python3 openCV/dataAugmentation.py &
export SPLIT_MOVIE_DATA_AUGMENTATION_SERVICE_PID_PID=$!

nohup python3 ModelML/learnResponse.py &
export SPLIT_MOVIE_LEARN_RESPONSE_SERVICE_PID=$!

cd -

exit 0