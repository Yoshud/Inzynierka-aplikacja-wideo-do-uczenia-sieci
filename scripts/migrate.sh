#!/usr/bin/env bash

cd "$(dirname "$0")/.."

mv mainServer/urls.py scripts/helpers/urls_orginal.py
mv scripts/helpers/urls_test.py mainServer/urls.py

mv mainServer/views.py scripts/helpers/views_orginal.py
mv scripts/helpers/views_test.py mainServer/views.py

python3 manage.py migrate

mv mainServer/views.py scripts/helpers/views_test.py
mv scripts/helpers/views_orginal.py mainServer/views.py

mv mainServer/urls.py scripts/helpers/urls_test.py
mv scripts/helpers/urls_orginal.py mainServer/urls.py

cd -