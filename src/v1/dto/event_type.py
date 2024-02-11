from enum import Enum


class EventType(Enum):
    """Webhook enum"""
    CLICK_ADS = 'clickAds'
    COMMENT = 'comment'
    LIKE = 'like'
