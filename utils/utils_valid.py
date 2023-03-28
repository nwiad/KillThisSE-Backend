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


