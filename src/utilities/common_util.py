from uuid import UUID


def is_valid_uuid(uuid, version=4):
    try:
        uuid_obj = UUID(uuid, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid


def extract_region(aws_arn: str) -> str:
    """
    Return region from aws_arn url
    example aws_arn arn:aws:kinesisvideo:ap-southeast-1:<aws_account>:channel/uuid/id
    default is ap-southeast-1
    """
    try:
        if not aws_arn.startswith("arn:aws"):
            return "ap-southeast-1"
        region = aws_arn.split(":")[3]
        return region
    except Exception as ex:
        return "ap-southeast-1"
