from datetime import datetime
from typing import List, Optional, Any
from pydantic import (
    BaseModel,
    constr,
    Json,
)


class WebhookModelInput(BaseModel):
    url: constr(max_length=512, min_length=1)
    api_key: constr(max_length=512)
    api_key_header_name: constr(max_length=128) = "Authorization"
    description: constr(max_length=256)
    enabled_alerts: List[constr(max_length=128)]
    enable: bool


class WebhookUpdateModelInput(BaseModel):
    url: Optional[constr(max_length=512)] = None
    api_key: Optional[constr(max_length=512)] = None
    api_key_header_name: Optional[constr(max_length=128)] = None
    description: Optional[constr(max_length=256)] = None
    enabled_alerts: Optional[List[constr(max_length=128)]] = None
    enable: Optional[bool] = None


class WebhookByIdModelInput(BaseModel):
    webhook_id: constr(max_length=128, min_length=1)


class SearchWebhookJsonModel(BaseModel):
    filters: Optional[Json[Any]]
