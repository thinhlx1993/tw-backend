import json
from datetime import datetime


def get_s3_folder_name(env_config):
    """returns S3 folder name based on env_config"""
    if env_config == 'https://dev.cognicept.systems':
        return 'development/'
    elif env_config == 'https://staging.cognicept.systems':
        return 'staging/'
    elif env_config == 'https://app.cognicept.systems':
        return 'production/'
    else:
        return ''


def process_alert_result(alert):
    """
    extract metadata from alert, remove unused data
    alert_type, notification_name robot_name, site, time and date, status
    """
    try:
        alert['created_at'] = datetime.fromtimestamp(float(alert.get('created_at'))).isoformat()
    except Exception as ex:
        # ignore this one, old data, for new data, it will be in iso format
        pass

    if alert.get("data", None) is not None:
        # va data
        va_alert = json.loads(alert["data"])
        alert['issue'] = va_alert.get("issue")
        alert['robot_name'] = va_alert.get("robot_name")
    response = {
        "alert_id": alert.get("alert_id"),
        "robot_name": alert.get("robot_name"),
        "created_at": alert.get("created_at"),
        "issue": alert.get("issue"),
        "status": alert.get("status"),
        "site_name": alert.get("site_name"),
        "alert_type": alert.get("alert_type"),
    }
    return response
