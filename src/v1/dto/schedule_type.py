from enum import Enum


class ScheduleType(Enum):
    """Schedule edit enum"""
    NON_REPEATING = 'non-repeating'
    REPEATING = 'repeating'
