import uuid
import base64
import io
import re

from dateutil import tz
from PIL import Image


def validate_uuid_list(uuid_list):
    """Checks for a valid UUID"""
    for uuid_str in uuid_list:
        try:
            uuid.UUID(uuid_str, version=4)
        except ValueError as e:
            raise ValueError("Invalid UUID: " + uuid_str)


def validate_timezone(timezone_str):
    """Checks for a valid timezone"""
    if tz.gettz(timezone_str):
        return True
    else:
        raise ValueError("Invalid timezone : " + timezone_str)


def validate_base64_image(image_string):
    # checking valid base64 image string
    try:
        cleaned_image_string = re.sub("^data:image\/[a-z]+;base64,( )*", "", image_string)
        image = base64.b64decode(cleaned_image_string)
        img = Image.open(io.BytesIO(image))
    except Exception:
        raise Exception('Invalid base64 image')

    # checking image format
    if img.format.lower() != "png":
        raise Exception(
            'Image is not valid, only \'base64\' image (png) is valid'
        )
