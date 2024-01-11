from datetime import datetime
from typing import List, Optional, Any
from pydantic import (
    BaseModel,
    constr,
    Json,
)


class SearchAlertsJsonModel(BaseModel):
    filters: Optional[Json[Any]] = {}
    last_evaluated_key: Optional[Json[Any]] = {}


class LastEvaluatedKeyModel(BaseModel):
    last_evaluated_key: Optional[Json[Any]] = {}
