class UserCheckException(Exception):
    """
    Exception thrown when check_user_exists throws an error
    """

    pass


class PasswordValidationException(Exception):
    """
    Exception thrown when validate_password throws an error
    """

    pass


class DatabaseQueryException(Exception):
    """
    Exception thrown when any queries on DB throw error
    """

    pass


class GetPermissionsException(Exception):
    """
    Exception thrown when get_user_permissions throws an error
    """

    pass


class GetRolesException(Exception):
    """
    Exception thrown when get_user_roles throws an error
    """

    pass


class JWTCreationException(Exception):
    """
    Exception thrown when create_access_token throws an error
    """

    pass


class NotificationTokenAddException(Exception):
    """
    Exception thrown when add_notification_token throws an error
    """

    pass


class UserCreateException(Exception):
    """
    Exception thrown when create_user throws an error
    """

    pass


class UserRoleMappingCreateException(Exception):
    """
    Exception thrown when create_user_role_mapping throws an error
    """

    pass


class UserUpdateException(Exception):
    """
    Exception thrown when update_user throws an error
    """

    pass


class NotFoundException(Exception):
    """
    Exception thrown when the target entity is not found
    """

    pass


class InvalidJWTToken(Exception):
    """
    Exception thrown when JWT token is invalid
    """

    pass
