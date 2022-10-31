#!/bin/bash
docker-compose run web python manage.py makemigrations --noinput
docker-compose run web python manage.py migrate --noinput
docker-compose run web python manage.py collectstatic --noinput
