import json
from django.http import HttpRequest
from rest_framework import viewsets

from utils.utils_request import request_failed, request_success
from utils.utils_require import CheckLogin

class MsgViewSet(viewsets.ViewSet):
    pass