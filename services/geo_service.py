# services/geo_service.py
import datetime
import logging
from typing import Optional

import pytz
from geopy.distance import great_circle
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from geopy.geocoders import Nominatim
from spacy.tokens import Doc
from timezonefinder import TimezoneFinder

from analysis_models import MatchMemory
from config import GEOLOCATOR_USER_AGENT, LONG_DISTANCE_THRESHOLD_KM

# --- Initialization ---
geolocator = Nominatim(user_agent=GEOLOCATOR_USER_AGENT)
tf = TimezoneFinder()
logger = logging.getLogger(__name__)

def update_geo_context(memory: MatchMemory, user_location_str: str, match_location_str: Optional[str], match_profile_doc: Doc):
    """
    Updates the memory object with geo-location data, including distance and timezone difference.
    """
    user_loc, match_loc = None, None
    try:
        user_loc = geolocator.geocode(user_location_str, timeout=5)
        if user_loc: memory.userLocation = user_loc.address
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        logger.warning(f"Geocoding for user location '{user_location_str}' failed: {e}")
        pass

    location_to_geocode = match_location_str or next((ent.text for ent in match_profile_doc.ents if ent.label_ == 'GPE'), None)
    if location_to_geocode:
        try:
            match_loc = geolocator.geocode(location_to_geocode, timeout=5)
            if match_loc: memory.matchLocation = match_loc.address
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            logger.warning(f"Geocoding for match location '{location_to_geocode}' failed: {e}")
            pass

    if user_loc and match_loc:
        distance = great_circle((user_loc.latitude, user_loc.longitude), (match_loc.latitude, match_loc.longitude)).kilometers
        memory.estimatedDistanceKm = round(distance, 2)
        memory.isLongDistance = distance > LONG_DISTANCE_THRESHOLD_KM
        user_tz_str = tf.timezone_at(lng=user_loc.longitude, lat=user_loc.latitude)
        match_tz_str = tf.timezone_at(lng=match_loc.longitude, lat=match_loc.latitude)
        if user_tz_str and match_tz_str:
            now_utc = datetime.datetime.now(pytz.utc)
            user_offset = now_utc.astimezone(pytz.timezone(user_tz_str)).utcoffset().total_seconds() / 3600
            match_offset = now_utc.astimezone(pytz.timezone(match_tz_str)).utcoffset().total_seconds() / 3600
            memory.timeZoneDifferenceHours = int(user_offset - match_offset)
