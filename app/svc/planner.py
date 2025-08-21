from datetime import datetime
import pytz
from app.schemas import UISettings, Location, GeoTimeInfo
from typing import Optional

def get_time_of_day(timezone_str: str) -> str:
    """Calculates the time of day for a given timezone."""
    try:
        user_timezone = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        user_timezone = pytz.utc  # Default to UTC if timezone is invalid

    now = datetime.now(user_timezone)
    hour = now.hour

    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"

def compute(ui_settings: UISettings, user_location: Location, match_location: Optional[Location] = None) -> GeoTimeInfo:
    """
    Calculates time of day, virtual/physical setting, and country difference.

    The `match_location` is optional as it might not always be available.
    """
    time_of_day = get_time_of_day(ui_settings.time_zone)

    # In a real system, this might be inferred from conversation context.
    # Hardcoded to True (virtual) for this implementation.
    is_virtual = True

    country_diff = False
    if match_location and user_location.country.lower() != match_location.country.lower():
        country_diff = True

    return GeoTimeInfo(
        time_of_day=time_of_day,
        is_virtual=is_virtual,
        country_difference=country_diff
    )
