from datetime import datetime
from typing import List, Optional
from pydantic import UUID4, BaseModel, constr, confloat, conint


class BoundingBox(BaseModel):
    top: confloat(ge=0, le=1)
    left: confloat(ge=0, le=1)
    height: confloat(ge=0, le=1)
    width: confloat(ge=0, le=1)


class Detection(BaseModel):
    feature: constr(min_length=1)
    value: constr(min_length=1)
    confidence: conint(ge=0, le=100)


class Inference(BaseModel):
    label: constr(min_length=1)
    category_id: constr(min_length=1)
    bounding_box: BoundingBox
    detections: List[Detection]
    is_duplicate: Optional[bool] = False


class VaInferenceInput(BaseModel):
    inference_list: List[Inference]
    image_url: str
    timestamp: datetime
    waypoint_id: Optional[UUID4] = None
    mission_instance_id: Optional[UUID4] = None
    robot_id: Optional[UUID4] = None
