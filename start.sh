#!/bin/sh
# 需要指定所有应用
python3 manage.py makemigrations user
python3 manage.py migrate

daphne -p 80 IMBackend.asgi:application

uwsgi --module=IMBackend.wsgi:application \
    --env DJANGO_SETTINGS_MODULE=IMBackend.settings \
    --master \
    --http :80 \
    --plugin python\
    --processes=5 \
    --harakiri=20 \
    --max-requests=5000 \
    --vacuum