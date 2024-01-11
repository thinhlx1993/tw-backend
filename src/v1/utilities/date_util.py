""""Util for all datetime operations"""
from datetime import datetime, timedelta
from dateutil import tz, parser


def get_time_before_n_minutes(date: datetime, minutes: int) -> datetime:
    return date - timedelta(minutes=minutes)


def get_time_after_n_minutes(date: datetime, minutes: int) -> datetime:
    return date + timedelta(minutes=minutes)


def convert_str_to_date_time(date: str, input_format: str) -> datetime:
    return datetime.strptime(date, input_format)


def convert_date_time_to_str(date: datetime, output_format: str) -> str:
    return datetime.strftime(date, output_format)


def convert_iso_str_to_date_time(date: str) -> datetime:
    return datetime.fromisoformat(date)


def convert_timezone(timestamp, source_tz_string, target_tz_string):
    """
    Converts the timestamp to required timezone

    :param str | datetime timestamp: timestamp to be converted
    :param str source_tz_string: current timezone string of the timestamp
    :param str target_tz_string: timezone string for the conversion
    """
    datetime_obj = (
        timestamp if isinstance(timestamp, datetime) else parser.parse(timestamp)
    )
    source_tz = tz.gettz(source_tz_string)
    target_tz = tz.gettz(target_tz_string)
    datetime_obj = datetime_obj.replace(tzinfo=source_tz)
    return datetime_obj.astimezone(target_tz)
