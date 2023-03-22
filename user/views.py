import json
from django.http import HttpRequest, HttpResponse

from user.models import User
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_time import get_timestamp

def startup(req: HttpRequest):
    return request_success({"message": "There is no exception in this library"})


def check_for_board_data(body):
    name = require(body, "name", "string", err_msg="Missing or error type of [name]")
    password = require(body, "password", "string", err_msg="Missing or error type of [password]")
    
    assert 0 < len(name) <= 50, "Bad length of [name]"
    assert 0 < len(password) <= 50, "Bad length of [password]"
       
    for i in name:
        pass
    
    return name, password


@CheckRequire
def user_register(req: HttpRequest):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))

        name, password = check_for_board_data(body)

        user = User.objects.filter(name=name).first()

        if user:
            return request_failed(1, "Username already exists", status_code=405)
        else :
            user = User(name=name, password=password)
            user.save()

        return request_success({"isCreate": True})
    
    else :
        return BAD_METHOD
    
@CheckRequire
def users(req: HttpRequest):
    if req.method == "GET":
        users = User.objects.all().order_by('register_time')
        return_data = {
            "users": [
                # Only provide required fields to lower the latency of
                # transmitting LARGE packets through unstable network
                return_field(user.serialize(), ["user_id", "name", "register_time"]) 
            for user in users],
        }
        return request_success(return_data)

    else :
        return BAD_METHOD
