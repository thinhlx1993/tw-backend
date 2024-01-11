from datetime import datetime


def to_datetime_obj(datetime_string):
    """ " Converts a datetime string to a datetime object"""
    try:
        datetime_string = datetime_string.replace("T", " ")
        datetime_obj = datetime.strptime(datetime_string, "%Y-%m-%d %H:%M:%S.%f")
        return datetime_obj
    except Exception as err:
        print(str(err))
        return None


def datetime_since(datetime_string):
    """ " Calculates datetime since the specified datetime string"""
    try:
        datetime_obj = to_datetime_obj(datetime_string)
        time_now = datetime.now()
        difference = time_now - datetime_obj
        return difference
    except Exception as err:
        print(str(err))
        return None


def datetime_now():
    return datetime.now()
