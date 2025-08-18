from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import pytz

def get_location_details(location_string):
    """
    Gets location details (city, state, country, timezone) from a location string.
    """
    try:
        geolocator = Nominatim(user_agent="dating_nlp_bot")
        location = geolocator.geocode(location_string, addressdetails=True, timeout=10)

        if not location:
            return None

        address = location.raw.get('address', {})
        city = address.get('city', address.get('town', address.get('village')))
        state = address.get('state')
        country = address.get('country')
        country_code = address.get('country_code')

        tz = pytz.country_timezones(country_code)[0] if country_code and country_code in pytz.country_timezones else None

        return {
            "address": location.address,
            "city": city,
            "state": state,
            "country": country,
            "timeZone": tz
        }
    except Exception as e:
        print(f"Error in geocoding: {e}")
        return None

def calculate_distance(location1_str, location2_str):
    """
    Calculates the distance in miles between two location strings.
    """
    try:
        geolocator = Nominatim(user_agent="dating_nlp_bot")
        loc1 = geolocator.geocode(location1_str, timeout=10)
        loc2 = geolocator.geocode(location2_str, timeout=10)

        if loc1 and loc2:
            return geodesic((loc1.latitude, loc1.longitude), (loc2.latitude, loc2.longitude)).miles
    except Exception as e:
        print(f"Error calculating distance: {e}")
        return None
    return None
