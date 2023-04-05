from user.models import User, Friendship, FriendshipRequest
from utils.utils_request import return_field


def isFriend(user1: User, user2: User):
    return Friendship.objects.filter(user_id=user1.user_id, friend_user_id=user2.user_id).first()


def requestExists(user1: User, user2: User):
    return FriendshipRequest.objects.filter(user_id=user1.user_id, friend_user_id=user2.user_id).first()


def addFriends(user1: User, user2: User):
    Friendship.objects.create(user_id=user1.user_id, friend_user_id=user2.user_id)
    Friendship.objects.create(user_id=user2.user_id, friend_user_id=user1.user_id)


def sendFriendRequest(user1: User, user2: User):
    FriendshipRequest.objects.create(user_id=user1.user_id, friend_user_id=user2.user_id)


def get_friends(user: User):
    friend_list = [x.friend_user_id for x in Friendship.objects.filter(user_id=user.user_id)]
    return friend_list
