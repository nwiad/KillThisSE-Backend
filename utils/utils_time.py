import datetime

def get_timestamp():
    return (datetime.datetime.now()).timestamp()

def get_datetime():
    return datetime.datetime.now() + datetime.timedelta(hours=48)
