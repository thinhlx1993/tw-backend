import json
from datetime import datetime


def generate_crontab_schedule(time_str=None, days=None):
    """
    Generates a crontab schedule string.

    :param time_str: Time in 'YYYY-MM-DDTHH:MM' format or None.
    :param days: List of days of the week as ['Monday', 'Tuesday', ...] or None for daily.
    :return: Crontab schedule string.
    """
    # Map days to crontab format (0-6, where 0 is Sunday)
    day_map = {
        'Sunday': '0',
        'Monday': '1',
        'Tuesday': '2',
        'Wednesday': '3',
        'Thursday': '4',
        'Friday': '5',
        'Saturday': '6'
    }

    # Default time (e.g., midnight) if time_str is None
    default_hour, default_minute = "0", "0"

    # Parse time_str to get hour and minute if provided
    if time_str:
        time_obj = datetime.strptime(time_str, "%Y-%m-%dT%H:%M")
        hour, minute = str(time_obj.hour), str(time_obj.minute)
    else:
        hour, minute = default_hour, default_minute

    # Determine the day field for crontab
    if days is None:
        day_field = '*'
    else:
        day_field = ','.join([day_map[day.capitalize()] for day in days if day.capitalize() in day_map])

    # Construct the crontab schedule string (minute hour day_of_month month day_of_week)
    crontab_schedule = f"{minute} {hour} * * {day_field}"

    return crontab_schedule
