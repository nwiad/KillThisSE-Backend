import json
from django.http import HttpRequest, HttpResponse

# Create your views here.

def startup(req: HttpRequest):
    return HttpResponse("This is a startup page for our IM project")
