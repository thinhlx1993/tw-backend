import json

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB, INET
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, text, func

from src import db


# Creating ROBOT class that maps to table 'robot'


class Robot(db.Model):
    """
    Model for robot table
    Attributes:
    'robot_id_uuid': Unique ID generated for each robot(UUID)
    'robot_code': Robot code (VARCHAR(30))
    'nick_name': Nick name of robot (VARCHAR(30))
    'property_id' : Property of robot(Big Integer)
    'status': Status of Robot(VARCHAR(30))
    'modified_by' : Modified by  (Big Integer)
    'modified_at': last modifed time of robot (DATETIME(TIMEZONE=TRUE))
    'last_heartbeat_at': Time at which last heartbeat was received (DATETIME(TIMEZONE=TRUE))
    'last_health_update': Time at which the last health status update was received (DATETIME(TIMEZONE=TRUE))
    'downtime_cost': Downtime Cost for robot (NUMERIC(8,2)))
    'activation_date': Activation date of robot(DATETIME(TIMEZONE=TRUE))
    'deactivation_date': Deactivation date of robot(DATETIME(TIMEZONE=TRUE))
    'is_active' = Active status of robot(BOOLEAN)
    'oem_id' : OEM code of robot  (UUID)
    'model_id' : Model of robot(UUID)
    'robot_ip_address' : ip address of robot (INET)
    'robot_computer_id' : Computer id to connect to zoho assist
    'external_url' : External url to connect
    'rosbridge_url' : Rosbridge url to connect
    'camerafeed_url' : Camera url to connect
    'is_deleted' : is deleted flag
    'robot_url' : Used by robot listener for robot connection
    'aws_channel_arn' : Used by webrtc agent for connection
    'aws_role_id': Unique Identifier for AWS role FK (UUID)
    'pilot_config': Pilot configuration for robot
    'init_config': Init configuration for robot
    'deploy_va_engine': telling VA Engine is deployed
    'va_engine_status': Can be `Pending` `Failed` `Deployed` `Uninstalled`
    'aws_kinesis_video_stream': Kinesis Video Stream
    """
    __tablename__ = "robot"

    robot_id = db.Column(
        db.String(128), primary_key=True,
        server_default=text("uuid_generate_v4()"), nullable=False)
    robot_code = db.Column(db.String(30))
    nick_name = db.Column(db.String(30))
    status = db.Column(db.String(30))
    modified_by = db.Column(db.BigInteger)
    downtime_cost = db.Column(db.Numeric(5, 2))
    activation_date = db.Column(db.DateTime(
        timezone=True), server_default=func.now())
    deactivation_date = db.Column(db.DateTime(timezone=True))
    is_active = db.Column(db.Boolean, server_default='true')
    deploy_va_engine = db.Column(db.Boolean, server_default='false')
    va_engine_status = db.Column(db.String(128), nullable=False, server_default='')
    robot_ip_address = db.Column(INET)
    robot_computer_id = db.Column(db.String(30))
    external_url = db.Column(db.String(255))
    rosbridge_url = db.Column(db.String(255))
    camerafeed_url = db.Column(db.String(255))
    robot_url = db.Column(db.String(255))
    aws_channel_arn = db.Column(db.String(500))
    aws_kinesis_video_stream = db.Column(db.String(512))
    is_deleted = db.Column(db.Boolean, server_default='false', nullable=False)
    rosbridge_support = db.Column(
        db.Boolean, server_default='false', nullable=False)
    modified_at = db.Column(db.DateTime(timezone=True),
                            server_default=func.now())
    last_heartbeat_at = db.Column(db.DateTime())
    last_health_update = db.Column(db.DateTime())
    pilot_config = db.Column(JSONB,
                             server_default='{\"roboops\":{\"map\":{\"topicId\":\"MAP\",\"topicType\":\"nav_msgs/OccupancyGrid\",\"topicName\":\"/map\"},\"laser_scan\":{\"topicId\":\"LASER_SCAN\",\"topicType\":\"sensor_msgs/LaserScan\",\"topicName\":\"/scan\"},\"move_base_goal\":{\"topicId\":\"MOVE_BASE_GOAL\",\"topicType\":\"geometry_msgs/PoseStamped\",\"topicName\":\"/move_base_simple/goal\"},\"navigation_plan\":{\"topicId\":\"NAVIGATION_PLAN\",\"topicType\":\"nav_msgs/Path\",\"topicName\":\"/move_base/NavfnROS/plan\"},\"navigation_stop\":{\"topicId\":\"NAVIGATION_STOP\",\"topicType\":\"actionlib_msgs/GoalID\",\"topicName\":\"/move_base/cancel\",\"topicMode\": \"PUBLISH\"},\"navigation_status\":{\"topicId\":\"NAVIGATION_STATUS\",\"topicType\":\"actionlib_msgs/GoalStatusArray\",\"topicName\":\"/move_base/status\",\"topicMode\":\"PUBLISH\"},\"navigation_result\":{\"topicId\":\"NAVIGATION_RESULT\",\"topicType\":\"move_base_msgs/MoveBaseActionResult\",\"topicName\":\"/move_base/result\",\"topicMode\":\"PUBLISH\"},\"localization_pose\":{\"topicId\":\"LOCALIZATION_POSE\",\"topicType\":\"geometry_msgs/PoseWithCovarianceStamped\",\"topicName\":\"/initialpose\"},\"occupancyGrid\":{\"localCostMap\":false,\"globalCostMap\":false,\"laser\":true}}}')
    status_details = db.Column(JSONB)
    init_config = db.Column(JSONB)
    mission = relationship("Mission", cascade="all,delete", backref="robot")
    mission_instances = relationship(
        'MissionInstance', cascade='all,delete', backref='robot')

    # Constructor initializing values

    def __init__(self, robot_code, model_id, nick_name,
                 property_id, oem_id, status, zendesk_id, modified_by=None,
                 downtime_cost=None, activation_date=None,
                 deactivation_date=None, is_active=None, robot_ip_address=None,
                 robot_computer_id=None, external_url=None, rosbridge_url=None,
                 camerafeed_url=None, aws_channel_arn=None, rosbridge_support=None,
                 pilot_config=None, deploy_va_engine=None):
        self.robot_code = robot_code
        self.model_id = model_id
        self.nick_name = nick_name
        self.property_id = property_id
        self.oem_id = oem_id
        self.status = status
        self.modified_by = modified_by
        self.downtime_cost = downtime_cost
        self.activation_date = activation_date
        self.deactivation_date = deactivation_date
        self.is_active = is_active
        self.robot_ip_address = robot_ip_address
        self.robot_computer_id = robot_computer_id
        self.external_url = external_url
        self.rosbridge_support = rosbridge_support
        self.rosbridge_url = rosbridge_url
        self.camerafeed_url = camerafeed_url
        self.aws_channel_arn = aws_channel_arn
        self.zendesk_id = zendesk_id
        self.pilot_config = pilot_config
        self.deploy_va_engine = deploy_va_engine

    # String representation of the model. Can be edited to show whatever
    # attributes we want to see.

    def __repr__(self):
        return json.dumps(
            {"robot_id": str(self.robot_id),
             "robot_code": str(self.robot_code),
             "model_id": str(self.model_id),
             "nick_name": self.nick_name,
             "property_id": str(self.property_id),
             "oem_id": str(self.oem_id),
             "status": self.status,
             "modified_by": self.modified_by,
             "modified_at": str(self.modified_at),
             "downtime_cost": str(self.downtime_cost),
             "activation_date": str(self.activation_date) if self.activation_date else None,
             "deactivation_date": str(self.deactivation_date) if self.deactivation_date else None,
             "is_active": self.is_active,
             "deploy_va_engine": self.deploy_va_engine,
             "va_engine_status": self.va_engine_status,
             "robot_ip_address": str(self.robot_ip_address) if self.robot_ip_address else None,
             "robot_computer_id": self.robot_computer_id,
             "external_url": str(self.external_url) if self.external_url else None,
             "rosbridge_url": str(self.rosbridge_url) if self.rosbridge_url else None,
             "camerafeed_url": str(self.camerafeed_url) if self.camerafeed_url else None,
             "robot_url": str(self.robot_url) if self.robot_url else None,
             "aws_channel_arn": str(self.aws_channel_arn) if self.aws_channel_arn else None,
             "aws_kinesis_video_stream": str(self.aws_kinesis_video_stream) if self.aws_kinesis_video_stream else None,
             "rosbridge_support": self.rosbridge_support,
             "is_deleted": self.is_deleted,
             "pilot_config": self.pilot_config,
             "init_config": self.init_config,
             "status_details": self.status_details,
             "aws_role_id": str(self.aws_role_id),
             "last_heartbeat_at": str(self.last_heartbeat_at),
             "last_health_update": str(self.last_health_update) if self.last_health_update else None
             })

    def repr_name(self):
        "Custom representation of the model"
        return {"robot_id": str(self.robot_id),
                "robot_code": str(self.robot_code).lower(),
                "robot_name": self.nick_name,
                "oem_id": str(self.oem_id) if self.oem_id else None,
                "model_id": str(self.model_id) if self.model_id else None,
                # "property_id": (self.property_id),
                "property_id": str(self.property_id) if self.property_id else None,
                "status": self.status,
                "deploy_va_engine": self.deploy_va_engine,
                "va_engine_status": self.va_engine_status,
                "downtime_cost": str(self.downtime_cost),
                "activation_date": str(self.activation_date) if self.activation_date else None,
                "deactivation_date": str(self.deactivation_date) if self.deactivation_date else None,
                "is_active": self.is_active,
                "robot_ip_address": str(self.robot_ip_address) if self.robot_ip_address else None,
                "robot_computer_id": str(self.robot_computer_id),
                "external_url": str(self.external_url) if self.external_url else None,
                "rosbridge_url": str(self.rosbridge_url) if self.rosbridge_url else None,
                "camerafeed_url": str(self.camerafeed_url) if self.camerafeed_url else None,
                "robot_url": str(self.robot_url) if self.robot_url else None,
                "aws_channel_arn": str(self.aws_channel_arn) if self.aws_channel_arn else None,
                "aws_kinesis_video_stream": str(
                    self.aws_kinesis_video_stream) if self.aws_kinesis_video_stream else None,
                "rosbridge_support": self.rosbridge_support,
                "is_deleted": self.is_deleted,
                "pilot_config": self.pilot_config,
                "init_config": self.init_config,
                "status_details": self.status_details,
                "aws_role_id": str(self.aws_role_id),
                "last_heartbeat_at": str(self.last_heartbeat_at) if self.last_heartbeat_at else None,
                "last_health_update": str(self.last_health_update) if self.last_health_update else None
                }

    def repr_label(self):
        return {
            'robot_id': str(self.robot_id),
            'robot_code': str(self.robot_code).lower(),
            'label': self.nick_name,
            'value': self.robot_code.lower(),
            'model_id': str(self.model_id),
            'modified_at': str(self.modified_at)
        }

    def repr_label_id(self):
        "Custom representation of the model."
        return {
            'value': str(self.robot_id),
            'label': self.nick_name
        }

    def repr_custom_label(self):
        # Sends representative custom field value for zendesk
        return {
            "name": self.nick_name,
            "value": self.robot_code.lower()
        }

    def repr_label_id_with_property(self):
        "Custom representation of the model"
        return {
            'property_id': str(self.property_id) if self.property_id else None,
            'value': str(self.robot_id),
            'label': self.nick_name
        }
