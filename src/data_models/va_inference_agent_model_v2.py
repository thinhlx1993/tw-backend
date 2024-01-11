from flask_restx import fields

from src.version_handler import api_version_2_agent

bounding_box_model = {
    "top": fields.Float(example=0.1),
    "left": fields.Float(example=0.78),
    "height": fields.Float(example=0.65),
    "width": fields.Float(example=0.9),
}

va_feature_detection_model = {
    "feature": fields.String(example="face"),
    "value": fields.String(example="John"),
    "confidence": fields.Integer(example=90, required=False),
}

va_inference_model = {
    "label": fields.String(example="Person", required=True),
    "category_id": fields.String(example="4ca4b5a9-4565-4e70-b6a5-5ad8e70d6155"),
    "confidence": fields.Integer(example=90, required=False),
    "bounding_box": fields.Nested(
        api_version_2_agent.model("bounding_box_model", bounding_box_model)
    ),
    "detections": fields.List(
        fields.Nested(
            api_version_2_agent.model(
                "va_feature_detection_model", va_feature_detection_model
            )
        )
    ),
}

va_alert_inference_model = {
    "inference_list": fields.List(
        fields.Nested(api_version_2_agent.model("va_tag_model", va_inference_model))
    ),
    "image_url": fields.String(example="https://image.png"),
    "timestamp": fields.DateTime(example="2020-03-10T04:25:09.15952"),
    "waypoint_id": fields.String(example="4ca4b5a9-4565-4e70-b6a5-5ad8e70d6155"),
    "mission_instance_id": fields.String(
        example="5ca4b5a9-4565-4e70-b6a5-5ad8e70d6155"
    ),
}

va_inference_api_model = api_version_2_agent.model(
    "va_alert_inference_model", va_alert_inference_model
)
