from datetime import datetime
from typing import List, Optional, Any
from pydantic import (
    BaseModel,
    constr,
    Json,
)

from src.enums.va_engine_status import VAEngineStatusEnums


class VAEngineStatusModel(BaseModel):
    va_engine_status: VAEngineStatusEnums


class VAEngineStatusPathParameters(BaseModel):
    robot_code: str
    teams_code: str