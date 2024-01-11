from enum import Enum


class UserRoleMappingType(Enum):
    """User type for API"""
    Users = "0c69b8ab-e118-467a-bada-63dd19a2cadd"
    Admin = "187fd4ad-4e79-419f-a0dd-b4344b473bf2"


class UserPlan(Enum):
    ProAccount = "pro"
    FreeAccount = "free"
