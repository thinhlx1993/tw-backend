import uuid

from flask_restx import fields

from src.version_handler import api_version_1_web

category_dict = {
    "va_category_id": fields.String(example=str(uuid.uuid4())),
    "name": fields.String(example="people_detection"),
}

# Category response model
category_list = {
    "data": fields.List(
        fields.Nested(api_version_1_web.model("category_row_dict", category_dict))
    )
}
category_ok_response_model = api_version_1_web.model(
    "category_ok_response_model", category_list
)
category_bad_response_model = api_version_1_web.model(
    "category_bad_response_model",
    {"message": fields.String(example="Error querying the DB")},
)
