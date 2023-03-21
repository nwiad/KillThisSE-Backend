import json
from django.http import HttpRequest, HttpResponse

# Create your views here.

def startup(req: HttpRequest):
    return HttpResponse("Congratulations! You have successfully installed the requirements. Go ahead!")