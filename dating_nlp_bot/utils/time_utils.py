from datetime import datetime
import pytz

def get_time_of_day(timezone_str):
    """
    Determines the time of day (Morning, Afternoon, Evening, Night) for a given timezone.
    """
    if not timezone_str or timezone_str not in pytz.all_timezones:
        return "Unknown"

    try:
        user_timezone = pytz.timezone(timezone_str)
        user_time = datetime.now(user_timezone)

        hour = user_time.hour

        if 5 <= hour < 12:
            return "Morning"
        elif 12 <= hour < 17:
            return "Afternoon"
        elif 17 <= hour < 21:
            return "Evening"
        else:
            return "Night"
    except pytz.UnknownTimeZoneError:
        return "Unknown"

def get_time_zone_difference(tz1_str, tz2_str):
    """
    Calculates the time zone difference in hours.
    """
    if not tz1_str or not tz2_str or tz1_str not in pytz.all_timezones or tz2_str not in pytz.all_timezones:
        return 0

    try:
        tz1 = pytz.timezone(tz1_str)
        tz2 = pytz.timezone(tz2_str)

        offset1 = datetime.now(tz1).utcoffset()
        offset2 = datetime.now(tz2).utcoffset()

        return abs(offset1.total_seconds() - offset2.total_seconds()) / 3600
    except pytz.UnknownTimeZoneError:
        return 0
