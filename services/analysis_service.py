import spacy
import datetime
import random
import re
from typing import List, Dict, Tuple, Optional

from spacy.matcher.dependencymatcher import defaultdict
from sqlalchemy.orm import Session
from geopy.geocoders import Nominatim
from geopy.distance import great_circle
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from timezonefinder import TimezoneFinder
import pytz
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline

from api_models import ScrapedData, UISettings
from analysis_models import (
    MessageAnalysis, SubtextAnalysis, QuestionInfo, FullConversationAnalysis, 
    MatchMemory, TopicDetails, GeoContext, LocationContext, PersonalityProfile,
    ResponseSuggestions, DateAnalysis, DateLogistics, SexualAnalysis, ConsentSignal
)
from utils.constants import (
    POSITIVE_WORDS, NEGATIVE_WORDS, AROUSAL_WORDS, VULNERABLE_WORDS,
    SEXUAL_WORDS, SEXUAL_EMOJIS, LOW_EFFORT_WORDS, GREETING_KEYWORDS,
    GEO_TRIGGERS, AMBIGUOUS_PHRASES, SARCASTIC_MARKERS, INTENSIFIERS,
    NEGATION_WORDS, INDIRECT_QUESTION_STARTERS, PLANNING_WORDS, SHIT_TEST_PATTERNS,
    DATE_KEYWORDS, COMMITMENT_LEVELS, RED_FLAGS
)
from db import crud
from config import *

# --- Initialization ---
# ... (omitting for brevity)

# --- Main Service Function ---

def run_full_conversation_analysis(db: Session, match_id: str, scraped_data: ScrapedData, ui_settings: UISettings) -> FullConversationAnalysis:
    history = scraped_data.conversationHistory
    analyzed_messages = [analyze_single_message(msg.content, msg.role, ui_settings.useEnhancedNlp) for msg in history]
    
    memory = _update_memory_from_history(history, analyzed_messages)
    geo_context = _get_geo_context(ui_settings.myLocation, scraped_data.theirLocationString, scraped_data.theirProfile)

    last_match_msg = next((m for m in reversed(analyzed_messages) if m.role == 'assistant'), None)
    conversation_state, _ = _determine_conversation_state_and_pacing(history, last_match_msg)
    suppress_greeting = _has_recent_greeting(history)

    for topic, details in memory.topics.items():
        if details.score < TOPIC_STATUS_AVOID_THRESHOLD:
            memory.avoidedTopics.append(topic)

    analysis = FullConversationAnalysis(
        conversationState=conversation_state,
        suppressGreeting=suppress_greeting,
        lastMessageAnalysis=last_match_msg,
        memory=memory,
        geoContext=geo_context
    )

    analysis.responseSuggestions = _get_response_suggestions(analysis)
    analysis.dateAnalysis = _get_date_analysis(analyzed_messages)
    analysis.sexualAnalysis = _get_sexual_analysis(analyzed_messages, memory)

    return analysis

# ... (omitting message analysis, memory update, etc. for brevity)

def _get_geo_context(user_location_str: str, match_location_str: Optional[str], match_profile: str) -> GeoContext:
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
            if 6 <= now.hour < 12: context_obj.timeOfDay = "Morning"
            elif 12 <= now.hour < 18: context_obj.timeOfDay = "Afternoon"
            elif 18 <= now.hour < 22: context_obj.timeOfDay = "Evening"
            else: context_obj.timeOfDay = "Late Night"

    try:
        user_loc = geolocator.geocode(user_location_str, timeout=5, addressdetails=True)
        if user_loc:
            _populate_location_context(user_loc, geo_context.userLocation)
    except (GeocoderTimedOut, GeocoderUnavailable): pass

    location_to_geocode = match_location_str or next((ent.text for ent in nlp(match_profile).ents if ent.label_ == 'GPE'), None)
    if location_to_geocode:
        try:
            match_loc = geolocator.geocode(location_to_geocode, timeout=5, addressdetails=True)
            if match_loc:
                _populate_location_context(match_loc, geo_context.matchLocation)
        except (GeocoderTimedOut, GeocoderUnavailable): pass

    if user_loc and match_loc:
        distance_km = great_circle((user_loc.latitude, user_loc.longitude), (match_loc.latitude, match_loc.longitude)).kilometers
        geo_context.distance["km"] = round(distance_km)
        geo_context.distance["miles"] = round(distance_km * 0.621371)
        if geo_context.userLocation.timeZone and geo_context.matchLocation.timeZone:
            user_offset = datetime.datetime.now(pytz.timezone(geo_context.userLocation.timeZone)).utcoffset().total_seconds() / 3600
            match_offset = datetime.datetime.now(pytz.timezone(geo_context.matchLocation.timeZone)).utcoffset().total_seconds() / 3600
            geo_context.timeZoneDifference = int(user_offset - match_offset)
        geo_context.countryDifference = geo_context.userLocation.country != geo_context.matchLocation.country

    return geo_context

# ... (omitting other helpers for brevity)
