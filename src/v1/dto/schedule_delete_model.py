from flask_restx import fields

from src.v1.dto.schedule_delete_type import ScheduleDeleteType

schedule_delete_model = {
    "current_schedule_timestamp": fields.DateTime(example="2023-07-10T10:00:00"),
    "delete_type": fields.String(
        example=ScheduleDeleteType.THIS_EVENT.value,
        enum=[x.value for x in ScheduleDeleteType],
    ),
}
