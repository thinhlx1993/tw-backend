from flask_restx import fields
from copy import deepcopy
from src.version_handler import api_version_1_web


endpoints_model = {
    "url": fields.String(example="https://customer.domain/api/v1/webhook/endpoint", required=True),
    "api_key": fields.String(example="uz2jOUoOHn486vAmKS6H", required=False),
    "api_key_header_name": fields.String(example="Authorization", required=False),
    "description": fields.String(example="Customer webhook listener", required=False),
    "enabled_alerts": fields.List(fields.String(example="webhook.va.positive_detection"), required=True),
    "enable": fields.Boolean(example=True, required=True)
}

webhook_endpoints_api_model = api_version_1_web.model(
    "webhook_endpoints_model", endpoints_model
)

update_endpoints_model = {
    "url": fields.String(example="https://customer.domain/api/v1/webhook/endpoint", required=False),
    "api_key": fields.String(example="uz2jOUoOHn486vAmKS6H", required=False),
    "api_key_header_name": fields.String(example="Authorization", required=False),
    "description": fields.String(example="Customer webhook listener", required=False),
    "enabled_alerts": fields.List(fields.String(example="webhook.va.positive_detection"), required=True),
    "enable": fields.Boolean(example=True, required=True)
}
webhook_update_endpoints_api_model = api_version_1_web.model(
    "webhook_endpoints_model", update_endpoints_model
)
