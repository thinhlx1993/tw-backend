from enum import Enum

class AggregateType(Enum):
    """Aggregate Type enum"""
    MIN = 'MIN'
    MAX = 'MAX'
    MEAN = 'MEAN'
    SUM = 'SUM' 
    COUNT = 'COUNT'