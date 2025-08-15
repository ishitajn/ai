import logging
import spacy
from sqlalchemy.orm import Session
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline

from api_models import ScrapedData, UISettings
from analysis_models import FullConversationAnalysis
from config import SPACY_MODEL, GEOLOCATOR_USER_AGENT
from utils.constants import TOPIC_STATUS_AVOID_THRESHOLD

from .analysis import (
    message_service,
    memory_service,
    geo_service,
    high_level_service,
    suggestion_service,
    date_service,
    sexual_service,
)

# --- Initialization ---
logger = logging.getLogger(__name__)

try:
    nlp = spacy.load(SPACY_MODEL)
except OSError:
    print(f"Downloading '{SPACY_MODEL}' model for spaCy...")
    from spacy.cli import download
    download(SPACY_MODEL)
    nlp = spacy.load(SPACY_MODEL)

geolocator = Nominatim(user_agent=GEOLOCATOR_USER_AGENT)
tf = TimezoneFinder()
vader_analyzer = SentimentIntensityAnalyzer()
topic_classifier = None
try:
    topic_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
except Exception as e:
    logger.error(f"Failed to load topic classifier model: {e}", exc_info=True)

# --- Main Service Function ---

def run_full_conversation_analysis(
    db: Session,
    match_id: str,
    scraped_data: ScrapedData,
    ui_settings: UISettings
) -> FullConversationAnalysis:
    logger.debug(f"Starting full analysis for match_id: {match_id}")
    logger.debug(f"Input Scraped Data: {scraped_data.model_dump_json(indent=2)}")
    logger.debug(f"Input UI Settings: {ui_settings.model_dump_json(indent=2)}")

    history = scraped_data.conversationHistory
    
    analyzed_messages = [
        message_service.analyze_single_message(
            text=msg.content,
            role=msg.role,
            use_enhanced_nlp=ui_settings.useEnhancedNlp,
            nlp=nlp,
            vader_analyzer=vader_analyzer
        ) for msg in history
    ]

    memory = memory_service.update_memory_from_history(
        history=history,
        analyzed_messages=analyzed_messages,
        nlp=nlp,
        topic_classifier=topic_classifier
    )

    geo_context = geo_service.get_geo_context(
        user_location_str=ui_settings.myLocation,
        match_location_str=scraped_data.theirLocationString,
        match_profile=scraped_data.theirProfile,
        geolocator=geolocator,
        tf=tf,
        nlp=nlp
    )

    last_match_msg = next((m for m in reversed(analyzed_messages) if m.role == 'assistant'), None)

    conversation_state, _ = high_level_service.determine_conversation_state_and_pacing(
        history=history,
        last_match_analysis=last_match_msg
    )

    suppress_greeting = high_level_service.has_recent_greeting(history)

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

    analysis.responseSuggestions = suggestion_service.get_response_suggestions(analysis)
    analysis.dateAnalysis = date_service.get_date_analysis(analyzed_messages, nlp)
    analysis.sexualAnalysis = sexual_service.get_sexual_analysis(analyzed_messages, memory)

    logger.debug(f"Final analysis object: {analysis.model_dump_json(indent=2)}")
    return analysis
