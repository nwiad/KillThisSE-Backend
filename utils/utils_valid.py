import re

from user.models import User

def name_valid(name: str):
    """
    check if name valid
    """
    return re.match(r"^[a-zA-Z0-9_]{3,16}$", name) is not None

def name_exist(name: str):
    """
    check if name already existed
    """
    user = User.objects.filter(name=name).first()
    return user

def password_valid(password: str):
    """
    check if password valid
    """
    return re.match(r"^[a-zA-Z0-9_]{6,16}$" ,password) is not None

def email_valid(email: str):
    """
    check if email valid
    """
    return re.match(r"^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$" ,email) is not None
