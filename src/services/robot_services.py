import datetime
import json
import time
import re
import math

from sqlalchemy import func, text, case
from sqlalchemy import sql, and_
from sentry_sdk import capture_exception
from flask_jwt_extended import get_jwt_claims

from src import db
from src.enums.va_engine_status import VAEngineStatusEnums
from src.models import Robot, Teams
from src.services import (
    teams_services,
    migration_services
)
from src.utilities import datetime_functions

Model = Robot
robot_columns = [m.key for m in Model.__table__.columns]


def get_site_details():
    """
    Get robot details for all sites
    """
    try:
        # session = create_session()
        query = db.session.query(Robot, Property, OEM).join(
            Property, Property.property_id == Robot.property_id).join(
                OEM, OEM.oem_id == Robot.oem_id).filter(Property.is_deleted == False).filter(
                    Robot.is_deleted == False).all()
        data = []
        for i in query:
            data_dict = {
                "cid": i[0].robot_code,
                "rid": str(i[0].robot_id),
                "robot_name": i[0].nick_name,
                "robot_original_name": i[0].robot_code,
                "robot_vendor":  i[2].name,
                "site": i[1].property_name,
                "site_contact": i[1].phone_number,
                "vendor_contact": i[2].contact,
                "site_type": i[1].property_type,
                "address": i[1].address,
                "DM": i[1].duty_manager
            }
            data.append(data_dict)
        db.session.flush()
    except Exception as e:
        db.session.rollback()
        capture_exception(e)
        # kill_session(session)
        return False, {"Message": str(e)}
    # kill_session(session)
    return True, data


def get_robot_details_from_name(robot_name):
    """
    Get robot details from name
    """
    try:
        # session = create_session()
        query = db.session.query(Robot, Property, OEM).join(
            Property, Property.property_id == Robot.property_id).join(
                OEM, OEM.oem_id == Robot.oem_id).filter(
                    func.lower(Robot.nick_name) == func.lower(robot_name)).filter(Robot.is_deleted == False).filter(
                        Property.is_deleted == False)
        data = []
        for i in query:
            data_dict = {
                "cid": i[0].robot_code,
                "rid": str(i[0].robot_id),
                "robot_name": i[0].nick_name,
                "robot_original_name": i[0].robot_code,
                "robot_vendor":  i[2].name,
                "site": i[1].property_name,
                "site_contact": i[1].phone_number,
                "vendor_contact": i[2].contact,
                "site_type": i[1].property_type,
                "address": i[1].address,
                "DM": i[1].duty_manager
            }
            data.append(data_dict)
        db.session.flush()
    except Exception as e:
        db.session.rollback()
        capture_exception(e)
        # kill_session(session)
        return False, {"Message": str(e)}
    # kill_session(session)
    return True, data


def get_connected_machines(property_id):
    """
    Get connected machines of a site
    """
    try:
        # session = create_session()
        data = []
        query = Robot.query.filter(Robot.property_id == property_id).filter(
            Robot.is_deleted == False).all()
        sub_query = Robot.query.with_entities(
            Robot.robot_id).filter(Robot.property_id == property_id).filter(Robot.is_deleted == False)
        tags = db.session.query(RobotTagMapping, RobotTag).with_entities(
            RobotTagMapping.robot_id, RobotTag.tag_value).join(
                RobotTag, RobotTag.tag_id == RobotTagMapping.tag_id).group_by(
                    RobotTagMapping.robot_id, RobotTag.tag_value).filter(RobotTagMapping.robot_id.in_(sub_query)).all()
        robot_tag_mapping = {}
        for i in tags:
            if i[0] in robot_tag_mapping.keys():
                robot_tag_mapping[i[0]].append(i[1])
            else:
                robot_tag_mapping[i[0]] = [i[1]]

        for i in query:
            data_dict = {
                "rid": str(i.robot_id),
                "robot_name": i.nick_name,
                "robot_original_name": i.robot_code,
                "robot_ip_address":  i.robot_ip_address,
                "tags": robot_tag_mapping.get(i.robot_id, [])
            }
            data.append(data_dict)
        db.session.flush()
    except Exception as e:
        db.session.rollback()
        capture_exception(e)
        # kill_session(session)
        return False, {"Message": str(e)}
    # kill_session(session)
    return True, data


def get_connected_machines_with_tags(property_id, tag):
    """
    Get connected machines with a tag
    """
    try:
        # session = create_session()
        data = []
        sub_query_tag = RobotTag.query.with_entities(
            RobotTag.tag_id).filter(RobotTag.tag_value.ilike(tag))
        sub_query = RobotTagMapping.query.with_entities(
            RobotTagMapping.robot_id).filter(RobotTagMapping.tag_id.in_(sub_query_tag))
        query = Robot.query.filter(and_(Robot.robot_id.in_(
            sub_query), Robot.property_id == property_id)).filter(Robot.is_deleted == False).filter(
                Property.is_deleted == False).all()
        tags = db.session.query(RobotTagMapping, RobotTag).with_entities(
            RobotTagMapping.robot_id, RobotTag.tag_value).join(
                RobotTag, RobotTag.tag_id == RobotTagMapping.tag_id).group_by(
                    RobotTagMapping.robot_id, RobotTag.tag_value).filter(RobotTagMapping.robot_id.in_(sub_query)).all()
        robot_tag_mapping = {}
        for i in tags:
            if i[0] in robot_tag_mapping.keys():
                robot_tag_mapping[i[0]].append(i[1])
            else:
                robot_tag_mapping[i[0]] = [i[1]]

        for i in query:
            data_dict = {
                "rid": str(i.robot_id),
                "robot_name": i.nick_name,
                "robot_original_name": i.robot_code,
                "robot_ip_address":  i.robot_ip_address,
                "tags": robot_tag_mapping.get(i.robot_id, [])
            }
            data.append(data_dict)
        db.session.flush()
    except Exception as e:
        db.session.rollback()
        capture_exception(e)
        # kill_session(session)
        return False, {"Message": str(e)}
    # kill_session(session)
    return True, data


def get_details_of_sites(filters):
    """
    Get property details of all sites
    """
    try:
        # session = create_session()
        query = db.session.query(Property).filter(
            Property.status == 'Active')
        if not filters:
            filters = {}
        filters["is_deleted"] = False
        status, query = dashboard_services.update_query(
            query, Property, filters=filters)
        if not status:
            return False, query
        query = query.all()
        data = []
        for i in query:
            data_dict = {
                "site": i.property_name,
                "site_contact": i.phone_number,
                "site_type": i.property_type,
                "address": i.address,
                "DM": i.duty_manager,
                "site_id": str(i.property_id),
                "site_code": i.property_code
            }
            data.append(data_dict)
        db.session.flush()
    except Exception as e:
        db.session.rollback()
        capture_exception(e)
        # kill_session(session)
        return False, {"Message": str(e)}
    # kill_session(session)
    return True, data


def get_live_machines(property_id):
    """
    Get live connected machines
    """
    try:
        time.sleep(3)
        data = ""
        count = 0
        query = Robot.query.filter(Robot.property_id == property_id).filter(
            Robot.is_deleted == False).all()
        for i in query:
            if i.robot_ip_address:
                data += i.robot_ip_address + "\n"
                count += 1
        output_data = {'ipAddress': data, 'count': count}
        db.session.flush()
    except Exception as e:
        db.session.rollback()
        capture_exception(e)
        return False, {"Message": str(e)}
    return True, output_data

def get_aws_role_arn(robot_id):
    """
    Get AWS role arn for robot
    :param robot_id: Robot ID to fetch AWS role arn foe
    :return str aws_role_arn: ARN for role
    """
    robot = (AwsRoles.query.join(Robot).filter(Robot.robot_id == robot_id).first())
    return robot.aws_role_arn

def create_robot(data):
    """
    Create agent
    
    :param str org_name: Name of teams
    :return bool, UUID: True, teams_id
    """
    try:
        new_robot = Robot(**data)
        db.session.add(new_robot)        
        db.session.flush()
        new_robot.external_url = "/robot/" + str(new_robot.robot_id)
        db.session.flush()
        return True, new_robot
    except Exception as e:
        db.session.rollback()
        capture_exception(e)
        raise


def get_robot_code_from_name(robot_name):
    """
    Generate valid robot code from robot name
    """
    # session = create_session()
    #Remove characters other than numbers and alphabets
    robot_code = re.sub(r"[^\w\s]", '_', robot_name)
    #Remove whitespaces with underscore
    robot_code = re.sub(r"\s+", '_', robot_code)
    status, data = get_robot_details_from_code(robot_code)
    if status != True or len(data) > 0:
        seq = 0
        is_valid_code = False
        # temp_code = robot_code
        while is_valid_code == False:
            seq += 1
            temp_code = robot_code + "_" + str(seq)
            status, data = get_robot_details_from_code(temp_code)
            if len(data) == 0:
                is_valid_code = True
                robot_code = temp_code
        robot_code = temp_code
    return robot_code


def get_robot_details_from_code(robot_code):
    """
    Get robot details from code
    """
    try:
        # session = create_session()
        query = db.session.query(Robot, Property).join(
            Property, Property.property_id == Robot.property_id).filter(
            func.lower(Robot.robot_code) == func.lower(robot_code))
        data = []
        for i in query:
            data_dict = {
                "cid": i[0].robot_code,
                "rid": str(i[0].robot_id),
                "robot_name": i[0].nick_name,
                "robot_original_name": i[0].robot_code
            }
            data.append(data_dict)
        db.session.flush()
    except Exception as e:
        db.session.rollback()
        capture_exception(e)
        # kill_session(session)
        return False, []
    # kill_session(session)
    return True, data

def get_robot_id_from_code(robot_code):
    """
    Retrieve robot_id from robot_code
    """
    try:
        robot = db.session.query(Robot).filter(func.lower(Robot.robot_code) == str(robot_code).lower()).first()
        return robot.robot_id
    except Exception as err:
        capture_exception(err)
        return None


def get_model_details(robot_id):
    """
    Get robot model details from robot_id
    :param robot_id: Identifier for robot
    :return model_details: Details of the model
    """
    model_details = RobotModel.query.join(Robot).filter(
        Robot.robot_id == robot_id).first()
    return model_details.repr_name()


def get_robot_details(robot_id):
    """
    Return true if robot exists in table
    :param robot_id: Identifier for robot
    :return bool: True if robot exists
    """
    try:
        robot_details = Robot.query.filter_by(robot_id=robot_id).first()
        return robot_details.repr_name() if robot_details else None
    except Exception as e:
        db.session.rollback()
        capture_exception(e)
        raise


def update_robot(data):
    """
    Update robot
    :param data: request body data
    """
    try:
        robotDetails = Robot.query.filter(
            Robot.robot_id == data.get("robot_id", None),
            Robot.is_deleted == False).first()
        if not robotDetails:
            db.session.rollback()
            return False, {"Message": "Invalid key"}
        # if property key is present    
        if data.get("property_id"):
            # update property_id in agent table
            agentDetails = Agent.query.filter_by(
                robot_id = data.get("robot_id", None)).all()
            for agent in agentDetails:
                agent.site_id=data["property_id"]

        # modify for VA Engine Deployment
        if data.get("deploy_va_engine", None) is not None:
            deploy_va_engine = data.get("deploy_va_engine", None)
            claims = get_jwt_claims()
            teams_id = claims['teams_id']
            teams_data = teams_services.get_teams(teams_id)
            teams_code = teams_data.teams_code
            robot_code = robotDetails.robot_code
            status = upgrade_va_engine(teams_code, robot_code, deploy_va_engine)
            robotDetails.va_engine_status = VAEngineStatusEnums.Pending.value
        # update metadata
        for i in data:
            setattr(robotDetails, i, data[i])
        robotDetails.modified_at = datetime.datetime.now()
        db.session.flush()
    except Exception as e:
        db.session.rollback()
        capture_exception(e)
        return False, {"message": str(e)}
    return True, {"message": "successfully updated record in database",     
                  "data" : json.loads(robotDetails.__repr__().replace("'", '"'))}


def upgrade_va_engine(teams_code, robot_code, deploy_va_engine):
    """
    Using for modify VA Engine, uninstall or install VA Engine on the k8s
    """
    script = "Install" if deploy_va_engine else "Uninstall"
    status = jenkins_services.trigger_deploy_va_engine(
        teams_code, robot_code, script
    )
    return status


def get_position_details_from_health_metrics(health_metrics):
    """
    Fetches position_details(posX, posY and posYaw) from health_metrics
    : param health_metrics: Dict containing current robot details
    : return pose: Dict containing x, y and yaw
    """
    if("posX" in health_metrics or "posY" in health_metrics 
                or "posyaw" in health_metrics):
        pose = {}
        pose["x"] = health_metrics.get("posX", None)
        pose["y"] = health_metrics.get("posY", None)
        pose["yaw"] = health_metrics.get("posYaw", None)
    else:
        pose = None
    return pose


def update_robot_status(robot_id, health_metrics):
    """
    Update the status_details of a robot
    :param robot_id: Unique identifier for robot
    :param health_metrics: Dict containing health metrics from robot
    :return bool: True if successful
    """
    try:
        robot_details = Robot.query.filter(Robot.robot_id==robot_id).first()
        if robot_details is None:
            raise Exception("Robot not found")

        # Form status_details json
        battery_details = get_battery_from_health_metrics(health_metrics)
        estop = (get_estop_from_health_metrics(health_metrics)
                        if 'eStop' in health_metrics else None)
        system_details = (get_system_details_from_health_metrics
                        (health_metrics))
        mission_details = get_mission_details_from_health_metrics(
            health_metrics)
        position_details = get_position_details_from_health_metrics(
            health_metrics)

        """
        @Author Thinh Le
        CRIS-10658 Retrieve map id attribute for active map of robot
        """
        active_map_id = get_active_map_id_from_health_metrics(
            health_metrics)

        if("cpuTemp" in health_metrics and health_metrics['cpuTemp']):
            temperature = health_metrics['cpuTemp']
        else:
            temperature = None

        # If there is no info regarding connected users to the robot then, 
        # users is set to None else it should be a list
        if "connectUsers" in health_metrics:
            users = health_metrics['connectUsers']
            if users:
                users = list(map(str, users.split(',')))
            else:
                users = []
        else:
            users = None

        status_details = {
            "battery": battery_details,
            "estop": estop,
            "pose": position_details,
            "system": system_details,
            "mission_details": mission_details,
            "temperature": temperature,
            "users": users,
            "active_map_id": active_map_id  # update active_map_id here
        }

        # now we need to check if at least one data is stale then what happens?
        # checks if the input payload is an empty string
        if ('timestamp' in health_metrics and health_metrics['timestamp']):
            robot_details.last_health_update = datetime_functions.datetime_now()
            
        robot_details.status_details = status_details
        db.session.flush()
        return True
    except Exception as err:
        db.session.rollback()
        capture_exception(err)
        raise


def get_battery_from_health_metrics(health_metrics):
    """
    Get battery details from health metrics
    :param health_metrics: Dict containing health metrics from robot
    """
    try:
        battery_details = {}
        charging_status = None
        if('batteryLevel' in health_metrics and
                        health_metrics['batteryLevel'] != ""):
            battery_details['level'] = health_metrics['batteryLevel']
        else:
            battery_details['level'] = None
        if('batteryStatus' in health_metrics and
                        health_metrics['batteryStatus'] != ""):
            battery_details['status'] = health_metrics['batteryStatus']
        else:
            battery_details['status'] = None

        if 'chargingStatus' in health_metrics:
            if health_metrics['chargingStatus'].lower() == "true" :
                charging_status = True
            elif health_metrics['chargingStatus'].lower() == "false":
                charging_status = False
        battery_details['charging'] = charging_status
        return battery_details
    except:
        raise




def get_estop_from_health_metrics(health_metrics):
    """
    Get boolean value of estop from health metrics
    :param health_metrics: Dict containing health metrics from robot
    """
    try:
        if health_metrics['eStop'].lower() == 'ok':
            return False
        elif  health_metrics['eStop'].lower() == 'error':
            return True
        elif health_metrics['eStop'] == "":
            return None
    except:
        raise


def get_system_details_from_health_metrics(health_metrics):
    """
    Get system details from health metrics
    :param health_metrics: Dict containing health metrics from robot
    """
    try:
        system_details = {}
        if('systemStatus' in health_metrics and 
                        health_metrics['systemStatus'] != ""):
            system_details['status'] = health_metrics['systemStatus']
        else:
            system_details['status'] = None

        # set localization
        if 'localizationStatus' in health_metrics:
            if health_metrics['localizationStatus'].lower() == 'true':
                system_details['localization'] = True
            elif  health_metrics['localizationStatus'].lower() == 'false':
                system_details['localization'] = False
        else :
            system_details['localization'] = None

        # set localization quality
        system_details['localizationQuality'] = health_metrics.get('localizationQuality', None)

        # set cpu        
        cpu = {}
        cpu['load'] = health_metrics.get('cpuLoad', None)
        cpu['temp'] = health_metrics.get('cpuTemp', None)
        cpu['usage'] = health_metrics.get('cpuUsage', None)

        system_details['cpu'] = cpu

        # set autonomous mode
        if 'autoMode' in health_metrics:
            if health_metrics['autoMode'].lower() == 'true':
                system_details['autonomous_mode'] = True
            elif  health_metrics['autoMode'].lower() == 'false':
                system_details['autonomous_mode'] = False
        else :
            system_details['autonomous_mode'] = None

        return system_details
    except:
        raise


def get_mission_details_from_health_metrics(health_metrics):
    """
    Fetches mission_details(mission_id and mission_name) from health_metrics
    : param health_metrics: Dict containing current robot details
    : return mission_details: Dict containing mission_id and mission_name
    """
    mission_details = {}
    if("missionName" in health_metrics and health_metrics["missionName"]):
        mission_name = health_metrics['missionName']
    else:
        mission_name = None
    if("missionId" in health_metrics and health_metrics['missionId']):
        mission_id = health_metrics['missionId']
    else:
        mission_id = None
    mission_details['mission_name'] = mission_name
    mission_details['mission_id'] = mission_id
    return mission_details


def get_active_map_id_from_health_metrics(health_metrics):
    """
    Fetches active_map_id from health_metrics
    : param health_metrics: Dict containing current robot details
    : return active_map_id: string active_map_id
    """
    if not isinstance(health_metrics, dict):
        return None
    return health_metrics.get('active_map_id', None)


def search_robots(page=0, per_page=None, sort_by="nick_name",
        sort_order="asc",filters=None, throw_error=True, custom_field=False,
        fields=['robot_id']):
    """Fetch robot list.

    :param filters : filters for log
    :param throw_error to use all fields in filter
    :return : status of response
    :return : robot list
    """
    data = []
    out_data = {}
    try:
        if not len(fields):
            fields = robot_columns
        if 'robot_id' not in fields:
            fields.append('robot_id')
        robot_column_list = []
        for column in fields:
            if column.strip() not in robot_columns:
                raise Exception("Invalid column name provided")
            else:
                robot_column_list.append(Robot.__table__.c[column.strip()])
        query = Robot.query.with_entities(*robot_column_list)
        if not filters:
            filters = {}
        get_stale_data = False
        if filters.get("get_stale_data") is not None:
            get_stale_data = filters["get_stale_data"]
        filters.pop("get_stale_data", None)
        filters["is_deleted"] = False
        sorting_order = sort_by + " " + sort_order
        status, query = dashboard_services.update_query(
            query, Robot, filters=filters, throw_error=throw_error)
        count = query.count()
        if not status:
            return False, query
        # Apply sorting
        if sorting_order:
            query = query.order_by(text(sorting_order))
        # Apply pagination
        if per_page and page:
            query = query.limit(per_page)
            query = query.offset(per_page*(page-1))
        query = query.all()
        if custom_field:
            data = [i.repr_label() for i in query]
        else:
            data = [format_robot_search(i,fields) for i in query]

        # Check for outdated robot status
        if not get_stale_data:
            for index, robot in enumerate(data):
                last_health_update = robot.get("last_health_update", None)
                if last_health_update is not None:
                    difference = datetime_functions.datetime_since(last_health_update)
                    difference_in_seconds = difference.seconds

                    # indicates robot details are outdated so send null
                    if difference_in_seconds > 180:
                        status_details = robot.get("status_details", {})
                        for key, value in status_details.items():
                            if type(value) is dict:
                                for inner_key in value:
                                    value[inner_key] = None
                            else:    
                                status_details[key] = None
                        robot["status_details"] = status_details
                        data[index] = robot
        out_data["data"] = data
        out_data["result_count"] = count
        if per_page:
            out_data["max_pages"] = math.ceil(count/per_page)
        db.session.flush()
    except Exception as err:
        db.session.rollback()
        capture_exception(err)
        return False, {"message": str(err)}
    return True, out_data


def format_robot_search(row, column_fields):
    """Format tuples from querying robots with entities.

    :param row: Row of data
    :return Dictionary containing data
    """
    out_data = {}
    for i in range(len(row)):
        if row[i]==None or isinstance(row[i], bool) or isinstance(row[i], dict):
            out_data[column_fields[i].strip()] = row[i]
        else:
            if column_fields[i].strip() == 'nick_name':
                out_data['robot_name'] = str(row[i])
            elif column_fields[i].strip() == 'robot_code':
                out_data['robot_code'] = str(row[i]).lower()
            else:
                out_data[column_fields[i].strip()] = str(row[i])
    return out_data


def update_va_engine_status(
    path_params,
    body
) -> (dict, bool):
    """
    Update VA Engine status
    :params: object path_params: object contains attrs teams_code and robot_code
    :params: VAEngineStatusEnums body: example this.va_engine_status.value = 'PENDING'
    return robot updated data
    """
    va_engine_status = body.va_engine_status.value
    teams_code = path_params.teams_code.replace("-", "_").lower()
    robot_code = path_params.robot_code.replace("-", "_").lower()

    # Query for teams using case-insensitive equality
    teams = Teams.query.filter(
        func.lower(Teams.teams_code) == teams_code
    ).first()
    if not teams:
        return {"message": f"cannot find this teams: {teams_code}"}, 400

    # set search path
    migration_services.set_search_path(teams.teams_id)
    robot_detail = Robot.query.filter(
        func.lower(Robot.robot_code) == robot_code
    ).first()
    if not robot_detail:
        return {"message": f"cannot find this robot: {robot_code}"}, 400

    if va_engine_status == VAEngineStatusEnums.FAILURE.value:
        # If Jenkins status is failure -> failed
        va_engine_status = VAEngineStatusEnums.Failed.value
    elif va_engine_status == VAEngineStatusEnums.SUCCESS.value:
        # If Jenkins status is success, determine based on deploy_va_engine
        va_engine_status = (
            VAEngineStatusEnums.Deployed.value
            if robot_detail.deploy_va_engine
            else VAEngineStatusEnums.Uninstalled.value
        )

    robot_detail.va_engine_status = va_engine_status
    db.session.flush()  # flush changes
    return robot_detail.repr_name(), 200
