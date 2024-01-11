from enum import Enum

class ScheduleDeleteType(Enum):
    """Schedule delete type enum"""
    THIS_EVENT = 'THIS_EVENT'
    THIS_EVENT_AND_FOLLOWING_EVENTS = 'THIS_EVENT_AND_FOLLOWING_EVENTS'
    ALL_EVENTS = 'ALL_EVENTS'
