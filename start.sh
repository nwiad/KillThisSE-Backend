#!/bin/sh
# 需要指定所有应用
python3 manage.py makemigrations user
python3 manage.py makemigrations msg
python3 manage.py migrate

daphne -b 0.0.0.0 -p 80 IMBackend.asgi:application

uwsgi --module=IMBackend.wsgi:application \
    --env DJANGO_SETTINGS_MODULE=IMBackend.settings \
    --master \
    --http=0.0.0.0:80 \
    --processes=5 \
    --harakiri=20 \
    --max-requests=5000 \
    --vacuum