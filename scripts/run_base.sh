#!/usr/bin/env bash
cd "$(dirname "$0")/../.."

docker stop db_split_movie_app
docker rm db_split_movie_app
docker run --name db_split_movie_app -p 18999:5432 -v $(pwd)/postgresData:/var/lib/postgresql/data -e POSTGRES_DB=movieDivideApp -d postgres

cd -

return 0