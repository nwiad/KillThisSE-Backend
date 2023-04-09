import json
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.hashers import make_password, check_password

from rest_framework import viewsets
from rest_framework.decorators import action

from user.models import User, Friendship, FriendshipRequest
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import CheckRequire, CheckLogin, require
from utils.utils_valid import *
from utils.utils_time import get_timestamp
from utils.utils_sessions import *
from utils.utils_friends import isFriend, requestExists, addFriends, sendFriendRequest
from utils.utils_constant import MAX_CHAR_LENGTH

def check_for_user_data(body):
    name = require(body, "name", "string", err_msg="Missing or error type of [name]")
    password = require(body, "password", "string", err_msg="Missing or error type of [password]")
    
    return name, password

class UserViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["POST"])
    def register(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))

        name, password = check_for_user_data(body)
        m_password = make_password(password)

        if not name_valid(name):
            return request_failed(1, "Illegal username")
        elif name_exist(name):
            return request_failed(2, "Username already exists")    
        elif not password_valid(password):
            return request_failed(3, "Illegal password")        
        else: # Successful Create
            user = User(name=name, password=m_password)
            user.save()
            # bind_session_id(get_session_id(req), user)

        return request_success({"Created": True})


    @action(detail=False, methods=["POST"])
    @CheckLogin
    def cancel_account(self, req: HttpRequest):
        user = verify_session_id(get_session_id(req))
        print("HI")
        
        if not user:
            return request_failed(1, "Not logged in", 400)

        user.delete()
        return request_success({"Deleted": True})

        
    @action(detail=False, methods=["POST"])
    def login(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))

        if verify_session_id(get_session_id(req)):
            return request_failed(4, "Already logged in")

        name, password = check_for_user_data(body)

        if name_valid(name):
            user = name_exist(name)
            if user and user.name == name:
                if check_password(password, user.password): # Password in database is encrypted
                    # Successful Login
                    bind_session_id(get_session_id(req), user)
                    return request_success({"Logged in": True})
                else:
                    return request_failed(3, "Wrong password")
            else:
                return request_failed(2, "User does not exist")
        else:
            return request_failed(1, "Illegal username")
        
            
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def logout(self, req: HttpRequest):
        disable_session_id(get_session_id(req))
        return request_success({'Logged out': True})

        
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def reset_name(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        user = verify_session_id(get_session_id(req))
        new_name = body.get('name')

        if not name_valid(new_name):
            return request_failed(2, "Illegal username")
        elif name_exist(new_name):
            return request_failed(3, "Username already exists")
        else:
            user.name = new_name

        user.save()
        return request_success({"Modified": True})
    

    @action(detail=False, methods=["POST"])
    @CheckLogin
    def reset_password(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        user = verify_session_id(get_session_id(req))
        old_password = body.get('old_pwd')
        new_password = body.get('new_pwd')

        if not check_password(old_password, user.password):
            return request_failed(2, "Wrong old password")

        if not password_valid(new_password):
            return request_failed(2, "Illegal password")
        else:
            user.password = make_password(new_password)
        
        user.save()
        return request_success({"Modified": True})
    
    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def reset_avatar(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        user = verify_session_id(get_session_id(req))
        new_avatar = body.get('avatar')

        user.avatar = new_avatar
        
        user.save()
        return request_success({"Modified": True})


    @action(detail=False, methods=["GET"])
    @CheckLogin
    def get_friend_requests(self, req: HttpRequest):
        user = verify_session_id(get_session_id(req))

        request_list = FriendshipRequest.objects.filter(friend_user_id=user.user_id)
        friend_id_list = [request.user_id for request in request_list]
        friend_list = [User.objects.filter(user_id=friend_id).first() for friend_id in friend_id_list]
        
        return_data = {
            "requests": [
                return_field(friend.serialize(), ["user_id", "name", "avatar"])
            for friend in friend_list
            ]
        }
        return request_success(return_data)

    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def send_friend_request(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        user = verify_session_id(get_session_id(req))

        friend_user_id = body.get('friend_user_id')
        friend = User.objects.filter(user_id=friend_user_id).first()
        if not friend:
            return request_failed(1, "Friend not exist")
        
        if isFriend(user, friend):
            return request_failed(2, "Already become friends")
        
        if requestExists(user, friend):
            return request_failed(3, "Request already exists")
        elif requestExists(friend, user): 
            addFriends(user, friend)
            requestExists(friend, user).delete()
            return request_success({"Become Friends": True})
        
        sendFriendRequest(user, friend)
        return request_success({"Send request": True})

    
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def respond_friend_request(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        user = verify_session_id(get_session_id(req))

        friend_user_id = body.get('friend_user_id')
        friend = User.objects.filter(user_id=friend_user_id)
        if not friend:
            return request_failed(1, "Friend not exist")
        
        if not requestExists(friend, user):
            return request_failed(2, "Friend request doesn't exist")
        response = body.get('response')

        if response == "accept":
            addFriends(user, friend)
            requestExists(friend, user).delete()
            return request_success({"Become Friends": True})
        elif response == "reject":
            requestExists(friend, user).delete()
            return request_success({"Become Friends": False})

        
    @action(detail=False, methods=["POST"])
    @CheckLogin
    def del_friend(self, req: HttpRequest):
        user = verify_session_id(get_session_id(req))
        body = json.loads(req.body.decode("utf-8"))
        friend_id = body.get('friend_user_id')
        friend = User.objects.filter(user_id=friend_id)

        if not friend:
            return request_failed(2, "Friend not exist")
        
        friendship = Friendship.objects.filter(user_id=user.user_id, friend_user_id=friend_id).first()
        if not friendship:
            return request_failed(3, "Not your friend")
        
        Friendship.objects.filter(user_id=user.user_id, friend_user_id=friend_id).delete()
        Friendship.objects.filter(user_id=friend_id, friend_user_id=user.user_id).delete()
        return request_success({"Deleted": True})
        
    
    @action(detail=False, methods=["GET"])
    @CheckLogin
    def get_profile(self, req: HttpRequest):
        user = verify_session_id(get_session_id(req))

        return_data = return_field(user.serialize(), ["user_id", "name", "avatar"])
        return request_success(return_data)
    
    
    @action(detail=False, methods=["GET"])
    @CheckLogin
    def search_by_id(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        friend_user_id = body.get('friend_user_id')
        friend = User.objects.filter(user_id=friend_user_id).first()

        if not friend:
            return request_failed(2, "Friend not exist")
        
        return_data = return_field(friend.serialize(), ["user_id", "name", "avatar"])
        return request_success(return_data)
    

    @action(detail=False, methods=["GET"])
    @CheckLogin
    def search_by_name(self, req: HttpRequest):
        body = json.loads(req.body.decode("utf-8"))
        friend_name = body.get('friend_name')
        friend = User.objects.filter(name=friend_name).first()

        if not friend:
            return request_failed(2, "Friend not exist")
        
        return_data = return_field(friend.serialize(), ["user_id", "name", "avatar"])
        return request_success(return_data)
    

    @action(detail=False, methods=["GET"])
    @CheckLogin
    def get_friends(self, req: HttpRequest):
        user = verify_session_id(get_session_id(req))
        friendship_list = Friendship.objects.filter(user_id=user.user_id)
        friend_id_list = [friendship.friend_user_id for friendship in friendship_list]
        friend_list = [User.objects.filter(user_id=friend_id).first() for friend_id in friend_id_list]

        return_data = {
            "friends": [
                return_field(friend.serialize(), ["user_id", "name", "avatar"])
            for friend in friend_list
            ]
        }
        return request_success(return_data)
    

    @action(detail=False, methods=["GET"])
    @CheckLogin
    def search_friend_by_id(self, req: HttpRequest):
        user = verify_session_id(get_session_id(req))
        body = json.loads(req.body.decode("utf-8"))
        friend_id = body.get('friend_id')

        friendship = Friendship.objects.filter(user_id=user.user_id, friend_user_id=friend_id)
        if not friendship:
            return request_failed(2, "Friend not exist")
        else:
            friend = User.objects.filter(user_id=friend_id).first()

        return_data = return_field(friend.serialize(), ["user_id", "name", "avatar"])

        return request_success(return_data)

        
    @action(detail=False, methods=["GET"])
    @CheckLogin
    def search_friend_by_name(self, req: HttpRequest):
        user = verify_session_id(get_session_id(req))
        body = json.loads(req.body.decode("utf-8"))
        friend_name = body.get('friend_name')

        friend = User.objects.filter(name=friend_name).first()
        if not friend:
            return request_failed(2, "Friend not exist")
        
        friend_id = friend.user_id
        friendship = Friendship.objects.filter(user_id=user.user_id, friend_user_id=friend_id)
        if not friendship:
            return request_failed(2, "Friend not exist")

        return_data = return_field(friend.serialize(), ["user_id", "name", "avatar"])

        return request_success(return_data)


    @action(detail=False, methods=["GET"])
    def users(self, req: HttpRequest):
        users = User.objects.all().order_by('register_time')
        return_data = {
            "users": [
                return_field(user.serialize(), ["user_id", "name", "avatar"]) 
            for user in users],
        }
        return request_success(return_data)
