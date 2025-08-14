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
    DATE_KEYWORDS, COMMITMENT_LEVELS
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

def _get_date_analysis(analyzed_messages: List[MessageAnalysis]) -> DateAnalysis:
    # ... (omitting for brevity)

def _get_sexual_analysis(analyzed_messages: List[MessageAnalysis], memory: MatchMemory) -> SexualAnalysis:
    """
    Analyzes the conversation for sexual dynamics.
    """
    sexual_analysis = SexualAnalysis()
    sexual_analysis.sexualTensionScore = memory.sexualTension

    match_sexual_intents = 0
    user_sexual_intents = 0

    for msg in analyzed_messages:
        text_lower = msg.content.lower()
        if "flirting_or_sexual" in msg.subtext.intents:
            if msg.role == 'assistant':
                match_sexual_intents += 1
            else:
                user_sexual_intents += 1

        # Simple consent signal check
        if msg.role == 'assistant' and "can't wait" in text_lower:
            sexual_analysis.consentSignals.append(
                ConsentSignal(type="enthusiastic_consent", evidence=msg.content)
            )

    if match_sexual_intents > 0:
        sexual_analysis.sexualIntentConfidence = min(0.95, 0.5 + (match_sexual_intents * 0.1))

    if user_sexual_intents > 0:
        sexual_analysis.reciprocityScore = min(1.0, match_sexual_intents / user_sexual_intents)

    # Placeholder logic for other fields
    if sexual_analysis.sexualTensionScore > 0.7:
        sexual_analysis.escalationPace = "fast"
    elif sexual_analysis.sexualTensionScore > 0.4:
        sexual_analysis.escalationPace = "moderate"
    else:
        sexual_analysis.escalationPace = "slow"

    sexual_analysis.sexualCommunicationStyle = "direct_and_explicit" if any(w in " ".join([m.content for m in analyzed_messages]) for w in SEXUAL_WORDS) else "implicit"

    return sexual_analysis

def _get_response_suggestions(analysis: FullConversationAnalysis) -> ResponseSuggestions:
    # ... (omitting for brevity)

# ... (omitting other helpers for brevity)
