import logging
import spacy
import datetime
from typing import Optional
from geopy.geocoders import Nominatim
from geopy.distance import great_circle
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from timezonefinder import TimezoneFinder
import pytz

from analysis_models import GeoContext

logger = logging.getLogger(__name__)

def get_geo_context(
    user_location_str: str,
    match_location_str: Optional[str],
    match_profile: str,
    geolocator: Nominatim,
    tf: TimezoneFinder,
    nlp: spacy.language.Language
) -> GeoContext:
    logger.debug(f"Getting geo context for user_location='{user_location_str}', match_location='{match_location_str}'")
    geo_context = GeoContext()
    user_loc, match_loc = None, None

    def _populate_location_context(location, context_obj):
        address = location.raw.get('address', {})
        context_obj.address = location.address
        context_obj.city = address.get('city', address.get('town', address.get('village')))
        context_obj.state = address.get('state')
        context_obj.country = address.get('country')
        context_obj.timeZone = tf.timezone_at(lng=location.longitude, lat=location.latitude)
        if context_obj.timeZone:
            now = datetime.datetime.now(pytz.timezone(context_obj.timeZone))
            if 6 <= now.hour < 12:
                context_obj.timeOfDay = "Morning"
            elif 12 <= now.hour < 18:
                context_obj.timeOfDay = "Afternoon"
            elif 18 <= now.hour < 22:
                context_obj.timeOfDay = "Evening"
            else:
                context_obj.timeOfDay = "Late Night"

    try:
        user_loc = geolocator.geocode(user_location_str, timeout=5, addressdetails=True)
        if user_loc:
            _populate_location_context(user_loc, geo_context.userLocation)
    except (GeocoderTimedOut, GeocoderUnavailable):
        pass

    location_to_geocode = match_location_str or next((ent.text for ent in nlp(match_profile).ents if ent.label_ == 'GPE'), None)
    if location_to_geocode:
        try:
            match_loc = geolocator.geocode(location_to_geocode, timeout=5, addressdetails=True)
            if match_loc:
                _populate_location_context(match_loc, geo_context.matchLocation)
        except (GeocoderTimedOut, GeocoderUnavailable):
            pass

    if user_loc and match_loc:
        distance_km = great_circle((user_loc.latitude, user_loc.longitude), (match_loc.latitude, match_loc.longitude)).kilometers
        geo_context.distance["km"] = round(distance_km)
        geo_context.distance["miles"] = round(distance_km * 0.621371)
        if geo_context.userLocation.timeZone and geo_context.matchLocation.timeZone:
            user_offset = datetime.datetime.now(pytz.timezone(geo_context.userLocation.timeZone)).utcoffset().total_seconds() / 3600
            match_offset = datetime.datetime.now(pytz.timezone(geo_context.matchLocation.timeZone)).utcoffset().total_seconds() / 3600
            geo_context.timeZoneDifference = int(user_offset - match_offset)
        geo_context.countryDifference = geo_context.userLocation.country != geo_context.matchLocation.country

    logger.debug(f"Geo context result: {geo_context.model_dump_json(indent=2)}")
    return geo_context
