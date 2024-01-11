from uuid import UUID


def is_valid_uuid(uuid, version=4):
    try:
        uuid_obj = UUID(uuid, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid