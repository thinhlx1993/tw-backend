from enum import Enum


class VAEngineStatusEnums(Enum):
    Pending = 'PENDING'
    Failed = 'FAILED'
    Deployed = 'DEPLOYED'
    Uninstalled = 'UNINSTALLED'
    FAILURE = 'FAILURE'
    SUCCESS = 'SUCCESS'
