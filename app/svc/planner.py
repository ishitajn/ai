from datetime import datetime
import pytz
from app.schemas import UISettings, Location, Geo, GeoLocationDetails
from typing import Optional
import asyncio

def _get_location_details(location: Location, timezone_str: str) -> GeoLocationDetails:
    """Helper to create GeoLocationDetails for a user or match."""
    try:
        timezone = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        # Default to UTC if the provided timezone string is invalid
        timezone = pytz.utc

    now = datetime.now(timezone)

    hour = now.hour
    if 5 <= hour < 12:
        time_of_day = "Morning"
    elif 12 <= hour < 17:
        time_of_day = "Afternoon"
    elif 17 <= hour < 21:
        time_of_day = "Evening"
    else:
        time_of_day = "Night"

    return GeoLocationDetails(
        city=location.city,
        country=location.country,
        timeOfDay=time_of_day,
        current_date_time=now.isoformat()
    )

async def compute(
    user_settings: UISettings,
    user_location: Location,
    # Match data is optional as it may not be available in the payload
    match_settings: Optional[UISettings] = None,
    match_location: Optional[Location] = None
) -> Geo:
    """
    Calculates the new, detailed Geo object. Made async to run concurrently.
    """
    # This is a fast, CPU-bound task, but we make it awaitable.
    await asyncio.sleep(0)

    user_geo_details = _get_location_details(user_location, user_settings.time_zone)

    # Handle optional match data gracefully
    if match_location and match_settings:
        match_geo_details = _get_location_details(match_location, match_settings.time_zone)
        country_diff = user_location.country.lower() != match_location.country.lower()

        # Calculate timezone difference in hours
        user_tz = pytz.timezone(user_settings.time_zone)
        match_tz = pytz.timezone(match_settings.time_zone)
        now_utc = datetime.now(pytz.utc)
        user_offset = user_tz.utcoffset(now_utc)
        match_offset = match_tz.utcoffset(now_utc)
        tz_diff_hours = int((user_offset - match_offset).total_seconds() / 3600)

        # The conversation is virtual if there is any geo-spatial difference
        is_virtual = bool(country_diff or (tz_diff_hours != 0))

    else:
        # If no match data, assume same location and no difference
        match_geo_details = GeoLocationDetails(
            city=user_location.city,
            country=user_location.country
        )
        country_diff = False
        tz_diff_hours = 0
        is_virtual = False

    return Geo(
        userLocation=user_geo_details,
        matchLocation=match_geo_details,
        isVirtual=is_virtual,
        timeZoneDifference=tz_diff_hours,
        countryDifference=country_diff
    )
