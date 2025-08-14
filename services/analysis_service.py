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
    MatchMemory, TopicDetails, GeoContext, LocationContext, PersonalityProfile
)
from utils.constants import (
    POSITIVE_WORDS, NEGATIVE_WORDS, AROUSAL_WORDS, VULNERABLE_WORDS,
    SEXUAL_WORDS, SEXUAL_EMOJIS, LOW_EFFORT_WORDS, GREETING_KEYWORDS,
    GEO_TRIGGERS, AMBIGUOUS_PHRASES, SARCASTIC_MARKERS, INTENSIFIERS,
    NEGATION_WORDS, INDIRECT_QUESTION_STARTERS, PLANNING_WORDS
)
from db import crud
from config import *

# --- Initialization ---
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
    print(f"Failed to load topic classifier model: {e}")

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

    return analysis

# --- Pipeline Router & Core Message Analysis ---

def analyze_single_message(text: str, role: str, use_enhanced_nlp: bool) -> MessageAnalysis:
    if not text:
        return MessageAnalysis(content="", role=role, subtext=SubtextAnalysis(), questionInfo=QuestionInfo())

    doc = nlp(text)
    subtext = _analyze_subtext_enhanced(doc) if use_enhanced_nlp else _analyze_subtext_legacy(doc)

    analysis_obj = MessageAnalysis(
        content=text,
        role=role,
        subtext=subtext,
        questionInfo=_analyze_question(doc),
        isLowEffort=_is_low_effort(text, doc),
        isGeoRelated=_detect_geo_related(doc),
        wordCount=len([token for token in doc if token.is_alpha])
    )
    analysis_obj.suggestedResponseStyle = _suggest_response_style(analysis_obj)
    return analysis_obj

# --- Sub-analysis Modules & Helper Functions ---

def _analyze_subtext_legacy(doc: spacy.tokens.Doc) -> SubtextAnalysis:
    text_lower = doc.text.lower()
    subtext = SubtextAnalysis(intents=[])
    valence, arousal = 0.0, 0.0
    for token in doc:
        token_text, multiplier = token.text.lower(), 1.0
        if token.i > 0 and doc[token.i - 1].text.lower() in INTENSIFIERS: multiplier *= INTENSIFIERS.get(doc[token.i - 1].text.lower(), 1.0)
        if any(c.dep_ == 'neg' for c in token.children) or (token.i > 0 and doc[token.i - 1].text.lower() in NEGATION_WORDS): multiplier *= -1
        if token_text in POSITIVE_WORDS: valence += POSITIVE_WORDS[token_text] * multiplier
        if token_text in NEGATIVE_WORDS: valence += NEGATIVE_WORDS[token_text] * multiplier
        if token_text in AROUSAL_WORDS: arousal += AROUSAL_WORDS[token_text]
    if any(w in text_lower for w in PLANNING_WORDS): subtext.intents.append("planning")
    if any(w in text_lower for w in SEXUAL_WORDS) or SEXUAL_EMOJIS.search(text_lower):
        subtext.intents.append("flirting_or_sexual")
    if any(p in text_lower for p in VULNERABLE_WORDS): subtext.isVulnerable = True
    if any(m in text_lower for m in SARCASTIC_MARKERS) and valence > 0: subtext.isSarcastic = True
    subtext.valence = max(-1, min(1, valence)); subtext.arousal = max(-1, min(1, arousal))
    subtext.isAmbiguous = any(phrase in text_lower for phrase in AMBIGUOUS_PHRASES)
    subtext.intents = list(set(subtext.intents))
    return subtext

def _analyze_subtext_enhanced(doc: spacy.tokens.Doc) -> SubtextAnalysis:
    subtext = _analyze_subtext_legacy(doc)
    vader_scores = vader_analyzer.polarity_scores(doc.text)
    subtext.valence = vader_scores['compound']
    subtext.arousal = 0.0
    return subtext

def _update_memory_from_history(history: List[ScrapedConversationMessage], analyzed_messages: List[MessageAnalysis]) -> MatchMemory:
    memory = MatchMemory()
    topic_sentiments = defaultdict(list)

    for i, msg in enumerate(analyzed_messages):
        if msg.questionInfo.isQuestion:
            memory.questionHistory.append(msg.content)

        if msg.role == 'assistant' and msg.subtext.valence > 0.8 and any(laugh in msg.content.lower() for laugh in ["lmao", "lol", "haha"]):
            if i > 0 and history[i-1].role == 'user':
                memory.insideJokes.append(history[i-1].content)

        doc = nlp(msg.content)
        topics = [c.text.lower() for c in doc.noun_chunks if len(c.text.split()) > 1 and not c.root.is_stop]

        for topic_text in topics:
            if topic_text not in memory.topics:
                memory.topics[topic_text] = TopicDetails()
            details = memory.topics[topic_text]
            details.mentions += 1
            topic_sentiments[topic_text].append(msg.subtext.valence)

    for topic, sentiments in topic_sentiments.items():
        avg_sentiment = sum(sentiments) / len(sentiments)
        mention_bonus = min(memory.topics[topic].mentions * 0.05, 0.2)
        memory.topics[topic].score = max(-1, min(1, avg_sentiment + mention_bonus))

    memory.dateArcPhase = "rapport"
    return memory

def _get_geo_context(user_location_str: str, match_location_str: Optional[str], match_profile: str) -> GeoContext:
    geo_context = GeoContext()
    user_loc, match_loc = None, None
    try:
        user_loc = geolocator.geocode(user_location_str, timeout=5)
        if user_loc:
            geo_context.userLocation.lat = user_loc.latitude
            geo_context.userLocation.lon = user_loc.longitude
            geo_context.userLocation.timeZone = tf.timezone_at(lng=user_loc.longitude, lat=user_loc.latitude)
    except (GeocoderTimedOut, GeocoderUnavailable): pass

    location_to_geocode = match_location_str or next((ent.text for ent in nlp(match_profile).ents if ent.label_ == 'GPE'), None)
    if location_to_geocode:
        try:
            match_loc = geolocator.geocode(location_to_geocode, timeout=5)
            if match_loc:
                geo_context.matchLocation.lat = match_loc.latitude
                geo_context.matchLocation.lon = match_loc.longitude
                geo_context.matchLocation.timeZone = tf.timezone_at(lng=match_loc.longitude, lat=match_loc.latitude)
        except (GeocoderTimedOut, GeocoderUnavailable): pass

    if user_loc and match_loc:
        distance_km = great_circle((user_loc.latitude, user_loc.longitude), (match_loc.latitude, match_loc.longitude)).kilometers
        geo_context.distance["km"] = round(distance_km)
        geo_context.distance["miles"] = round(distance_km * 0.621371)
        if geo_context.userLocation.timeZone and geo_context.matchLocation.timeZone:
            user_offset = datetime.datetime.now(pytz.timezone(geo_context.userLocation.timeZone)).utcoffset().total_seconds() / 3600
            match_offset = datetime.datetime.now(pytz.timezone(geo_context.matchLocation.timeZone)).utcoffset().total_seconds() / 3600
            geo_context.timeZoneDifference = int(user_offset - match_offset)
            geo_context.countryDifference = geo_context.userLocation.timeZone.split('/')[0] != geo_context.matchLocation.timeZone.split('/')[0]
    return geo_context

def _detect_geo_related(doc: spacy.tokens.Doc) -> bool:
    return any(token.lemma_ in GEO_TRIGGERS for token in doc)

def _suggest_response_style(analysis: MessageAnalysis) -> str:
    if analysis.subtext.isSarcastic: return "witty"
    if "flirting_or_sexual" in analysis.subtext.intents: return "playful"
    if analysis.subtext.isVulnerable: return "supportive"
    if analysis.questionInfo.isQuestion: return "direct"
    if analysis.subtext.valence > 0.5: return "charming"
    return "casual"

def _analyze_question(doc: spacy.tokens.Doc) -> QuestionInfo:
    text_lower = doc.text.lower().strip()
    if text_lower.endswith('?'): return QuestionInfo(isQuestion=True, count=1, type="open" if doc[0].tag_ in ("WP", "WRB") else "closed")
    if any(text_lower.startswith(s) for s in INDIRECT_QUESTION_STARTERS): return QuestionInfo(isQuestion=True, count=1, type="indirect")
    return QuestionInfo()

def _is_low_effort(text: str, doc: spacy.tokens.Doc) -> bool:
    text_clean = text.strip().lower()
    if len(doc) < 4 and text_clean in LOW_EFFORT_WORDS: return True
    return all(w.strip(".,!?-") in LOW_EFFORT_WORDS for w in text_clean.split())

def _determine_conversation_state_and_pacing(history: List[ScrapedConversationMessage], last_match_analysis: Optional[MessageAnalysis]) -> Tuple[str, str]:
    if not history: return "OPENER", "normal"
    return "ACTIVE_CONVO", "normal"

def _has_recent_greeting(history: List[ScrapedConversationMessage]) -> bool:
    now = datetime.datetime.now(datetime.timezone.utc)
    for msg in reversed(history):
        try:
            msg_date = datetime.datetime.fromisoformat(msg.date.replace("Z", "+00:00"))
            if (now - msg_date).total_seconds() > 12 * 3600: break
            if msg.role == 'user' and any(greet in msg.content.lower() for greet in GREETING_KEYWORDS): return True
        except (ValueError, TypeError, AttributeError, IndexError): continue
    return False
