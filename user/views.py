import json
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.hashers import make_password, check_password

from user.models import User
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.utils_valid import *
from utils.utils_time import get_timestamp

@CheckRequire
def startup(req: HttpRequest):
    return request_success({"message": "There is no exception in this library"})


def check_for_user_data(body):
    name = require(body, "name", "string", err_msg="Missing or error type of [name]")
    password = require(body, "password", "string", err_msg="Missing or error type of [password]")
    
    return name, password


@CheckRequire
def user_register(req: HttpRequest):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))

        name, password = check_for_user_data(body)
        m_password = make_password(password)

        if not name_valid(name):
            return request_failed(1, "不合法的用户名")
        elif name_exist(name):
            return request_failed(2, "用户名已经存在")    
        elif not password_valid(password):
            return request_failed(3, "不合法的密码")        
        else:
            user = User(name=name, password=m_password)
            user.save()

        return request_success({"isCreate": True})
    
    else :
        return BAD_METHOD
    
@CheckRequire
def user_login(req: HttpRequest):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))

        name, password = check_for_user_data(body)

        if name_valid(name):
            user = name_exist(name)
            if user and user.name == name:
                if check_password(password, user.password):
                    return request_success({"Logged in": True})
                else:
                    return request_failed(3, "Wrong password")
            else:
                return request_failed(2, "User does not exist")
        else:
            return request_failed(1, "Illegal username")
    
@CheckRequire
def users(req: HttpRequest):
    if req.method == "GET":
        users = User.objects.all().order_by('register_time')
        return_data = {
            "users": [
                return_field(user.serialize(), ["user_id", "name", "register_time"]) 
            for user in users],
        }
        return request_success(return_data)

    else :
        return BAD_METHOD
