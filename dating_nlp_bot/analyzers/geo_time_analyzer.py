from ..utils.location_utils import get_location_details, calculate_distance
from ..utils.time_utils import get_time_of_day, get_time_zone_difference

def analyze_geo_time(user_location_str, match_location_str):
    """
    Analyzes geographic and time-based context.
    """
    user_location = get_location_details(user_location_str)
    match_location = get_location_details(match_location_str)

    # Create default structures to avoid KeyErrors
    user_location_data = {"address": user_location_str, "city": None, "state": None, "country": None, "timeZone": None}
    match_location_data = {"address": match_location_str, "city": None, "state": None, "country": None, "timeZone": None}

    if user_location:
        user_location_data.update(user_location)
    if match_location:
        match_location_data.update(match_location)

    user_location_data["timeOfDay"] = get_time_of_day(user_location_data["timeZone"])
    match_location_data["timeOfDay"] = get_time_of_day(match_location_data["timeZone"])

    distance = calculate_distance(user_location_str, match_location_str)
    tz_diff = get_time_zone_difference(user_location_data["timeZone"], match_location_data["timeZone"])
    country_diff = user_location_data["country"] != match_location_data["country"] if user_location_data["country"] and match_location_data["country"] else False

    is_virtual = False
    if distance is not None and distance > 100: # Over 100 miles is likely virtual
        is_virtual = True
    if country_diff:
        is_virtual = True

    return {
        "userLocation": user_location_data,
        "matchLocation": match_location_data,
        "distance_miles": distance,
        "timeZoneDifference": tz_diff,
        "countryDifference": country_diff,
        "isVirtual": is_virtual
    }
