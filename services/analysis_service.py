import logging
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
    print(f"Failed to load topic classifier model: {e}")

# --- Main Service Function ---

def run_full_conversation_analysis(db: Session, match_id: str, scraped_data: ScrapedData, ui_settings: UISettings) -> FullConversationAnalysis:
    logger.debug(f"Starting full analysis for match_id: {match_id}")
    logger.debug(f"Input Scraped Data: {scraped_data.model_dump_json(indent=2)}")
    logger.debug(f"Input UI Settings: {ui_settings.model_dump_json(indent=2)}")

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

    logger.debug(f"Final analysis object: {analysis.model_dump_json(indent=2)}")
    return analysis

# --- Pipeline Router & Core Message Analysis ---

def analyze_single_message(text: str, role: str, use_enhanced_nlp: bool) -> MessageAnalysis:
    logger.debug(f"Analyzing single message. Role: {role}, Enhanced NLP: {use_enhanced_nlp}, Content: '{text}'")
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
    logger.debug(f"Single message analysis result: {analysis_obj.model_dump_json(indent=2)}")
    return analysis_obj

# --- Sub-analysis Modules & Helper Functions ---

def _analyze_subtext_legacy(doc: spacy.tokens.Doc) -> SubtextAnalysis:
    logger.debug(f"Analyzing subtext (legacy) for: '{doc.text}'")
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
    logger.debug(f"Subtext (legacy) result: {subtext.model_dump_json(indent=2)}")
    return subtext

def _analyze_subtext_enhanced(doc: spacy.tokens.Doc) -> SubtextAnalysis:
    logger.debug(f"Analyzing subtext (enhanced) for: '{doc.text}'")
    subtext = _analyze_subtext_legacy(doc)
    vader_scores = vader_analyzer.polarity_scores(doc.text)
    logger.debug(f"Vader scores: {vader_scores}")
    subtext.valence = vader_scores['compound']
    subtext.arousal = 0.0
    logger.debug(f"Subtext (enhanced) result: {subtext.model_dump_json(indent=2)}")
    return subtext

def _update_memory_from_history(history: List[ScrapedConversationMessage], analyzed_messages: List[MessageAnalysis]) -> MatchMemory:
    memory = MatchMemory()
    topic_sentiments = defaultdict(list)
    user_messages = [m for m in analyzed_messages if m.role == 'user']
    match_messages = [m for m in analyzed_messages if m.role == 'assistant']

    investment_delta = 0
    if match_messages and user_messages:
        last_match_msg, last_user_msg = match_messages[-1], user_messages[-1]
        if last_match_msg.questionInfo.isQuestion: investment_delta += 0.2
        if last_user_msg.questionInfo.isQuestion and not last_match_msg.questionInfo.isQuestion: investment_delta -= 0.15
        if last_match_msg.wordCount >= last_user_msg.wordCount * 0.8: investment_delta += 0.1
        else: investment_delta -= 0.1
        if last_match_msg.isLowEffort: investment_delta -= 0.3
    logger.debug(f"Calculated investment delta: {investment_delta}")
    memory.investmentScore = max(-1, min(1, (memory.investmentScore * 0.8) + investment_delta))
    logger.debug(f"Updated investment score: {memory.investmentScore}")

    total_valence, tension_delta = 0, 0
    for msg in analyzed_messages:
        if msg.role == 'assistant':
            total_valence += msg.subtext.valence
        if "flirting_or_sexual" in msg.subtext.intents:
            tension_delta += 0.3
    if user_messages and match_messages and "flirting_or_sexual" in user_messages[-1].subtext.intents and match_messages[-1].subtext.valence < -0.2:
        tension_delta -= 0.5
    logger.debug(f"Calculated sexual tension delta: {tension_delta}")
    memory.sexualTension = max(0, min(1, (memory.sexualTension * 0.85) + tension_delta))
    logger.debug(f"Updated sexual tension: {memory.sexualTension}")

    avg_valence = total_valence / len(match_messages) if match_messages else 0
    rapport_bonus = min(len(match_messages) / 10, 0.5)
    memory.rapportScore = max(0, min(1, (avg_valence + 1) / 2 + rapport_bonus))
    logger.debug(f"Calculated rapport score: {memory.rapportScore} (avg_valence: {avg_valence}, bonus: {rapport_bonus})")

    match_messages_text = " ".join([msg.content for msg in match_messages])
    if topic_classifier and match_messages_text:
        memory.personalityProfile = _get_personality_profile(match_messages_text)

    memory.redFlags = _detect_red_flags(analyzed_messages)

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

    memory.dateArcPhase = "rapport" # Simplified
    logger.debug(f"Final memory object: {memory.model_dump_json(indent=2)}")
    return memory

def _get_personality_profile(text: str) -> PersonalityProfile:
    logger.debug(f"Getting personality profile for text: '{text[:100]}...'")
    profile = PersonalityProfile()
    if not topic_classifier:
        logger.debug("Topic classifier not available, returning empty profile.")
        return profile
    trait_labels = {
        "extraversion": "extroverted, outgoing, and sociable language",
        "agreeableness": "agreeable, compassionate, and friendly language",
        "openness": "language showing openness, imagination, and curiosity"
    }
    try:
        result = topic_classifier(text, list(trait_labels.values()), multi_label=True)
        label_to_trait = {v: k for k, v in trait_labels.items()}
        for label, score in zip(result['labels'], result['scores']):
            setattr(profile, label_to_trait[label], round(score, 2))
    except Exception as e:
        logger.error(f"Error during personality trait classification: {e}", exc_info=True)
    logger.debug(f"Personality profile result: {profile.model_dump_json(indent=2)}")
    return profile

def _detect_red_flags(analyzed_messages: List[MessageAnalysis]) -> List[str]:
    logger.debug("Detecting red flags.")
    flags = []
    for msg in analyzed_messages:
        text_lower = msg.content.lower()
        for flag_phrase in RED_FLAGS:
            if flag_phrase in text_lower:
                flags.append(flag_phrase)
    unique_flags = list(set(flags))
    logger.debug(f"Red flags detected: {unique_flags}")
    return unique_flags

def _get_geo_context(user_location_str: str, match_location_str: Optional[str], match_profile: str) -> GeoContext:
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
            if 6 <= now.hour < 12: context_obj.timeOfDay = "Morning"
            elif 12 <= now.hour < 18: context_obj.timeOfDay = "Afternoon"
            elif 18 <= now.hour < 22: context_obj.timeOfDay = "Evening"
            else: context_obj.timeOfDay = "Late Night"
    try:
        user_loc = geolocator.geocode(user_location_str, timeout=5, addressdetails=True)
        if user_loc: _populate_location_context(user_loc, geo_context.userLocation)
    except (GeocoderTimedOut, GeocoderUnavailable): pass
    location_to_geocode = match_location_str or next((ent.text for ent in nlp(match_profile).ents if ent.label_ == 'GPE'), None)
    if location_to_geocode:
        try:
            match_loc = geolocator.geocode(location_to_geocode, timeout=5, addressdetails=True)
            if match_loc: _populate_location_context(match_loc, geo_context.matchLocation)
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

    logger.debug(f"Geo context result: {geo_context.model_dump_json(indent=2)}")
    return geo_context

def _get_date_analysis(analyzed_messages: List[MessageAnalysis]) -> DateAnalysis:
    logger.debug("Getting date analysis.")
    date_analysis = DateAnalysis()
    for msg in reversed(analyzed_messages):
        text_lower = msg.content.lower()
        if any(word in text_lower for word in PLANNING_WORDS):
            date_analysis.isDatePlanned = True
            for keyword, date_type in DATE_KEYWORDS.items():
                if keyword in text_lower:
                    date_analysis.dateType = date_type
                    if date_type == "virtual": date_analysis.isVirtual = True
                    break
            for level, phrases in COMMITMENT_LEVELS.items():
                if any(phrase in text_lower for phrase in phrases):
                    date_analysis.dateCommitmentLevel = level
                    break
            doc = nlp(msg.content)
            for ent in doc.ents:
                if ent.label_ in ("TIME", "DATE"): date_analysis.dateLogistics.time = ent.text
                if ent.label_ in ("ORG", "FAC"): date_analysis.dateLogistics.venue = ent.text
            if date_analysis.dateCommitmentLevel != "none": break
    logger.debug(f"Date analysis result: {date_analysis.model_dump_json(indent=2)}")
    return date_analysis

def _get_sexual_analysis(analyzed_messages: List[MessageAnalysis], memory: MatchMemory) -> SexualAnalysis:
    logger.debug("Getting sexual analysis.")
    sexual_analysis = SexualAnalysis()
    sexual_analysis.sexualTensionScore = memory.sexualTension
    match_sexual_intents = sum(1 for msg in analyzed_messages if msg.role == 'assistant' and "flirting_or_sexual" in msg.subtext.intents)
    user_sexual_intents = sum(1 for msg in analyzed_messages if msg.role == 'user' and "flirting_or_sexual" in msg.subtext.intents)
    for msg in analyzed_messages:
        if msg.role == 'assistant' and "can't wait" in msg.content.lower():
            sexual_analysis.consentSignals.append(ConsentSignal(type="enthusiastic_consent", evidence=msg.content))
    if match_sexual_intents > 0:
        sexual_analysis.sexualIntentConfidence = min(0.95, 0.5 + (match_sexual_intents * 0.1))
    if user_sexual_intents > 0:
        sexual_analysis.reciprocityScore = min(1.0, match_sexual_intents / user_sexual_intents)
    if sexual_analysis.sexualTensionScore > 0.7: sexual_analysis.escalationPace = "fast"
    elif sexual_analysis.sexualTensionScore > 0.4: sexual_analysis.escalationPace = "moderate"
    else: sexual_analysis.escalationPace = "slow"
    sexual_analysis.sexualCommunicationStyle = "direct_and_explicit" if any(w in " ".join(m.content for m in analyzed_messages) for w in SEXUAL_WORDS) else "implicit"
    logger.debug(f"Sexual analysis result: {sexual_analysis.model_dump_json(indent=2)}")
    return sexual_analysis

def _get_response_suggestions(analysis: FullConversationAnalysis) -> ResponseSuggestions:
    logger.debug("Getting response suggestions.")
    suggestions = ResponseSuggestions()
    memory = analysis.memory
    last_match_msg = analysis.lastMessageAnalysis
    suggestions.suggestedNextAction = _get_suggested_next_action(memory, last_match_msg)
    if memory.dateArcPhase == "escalation": suggestions.tone = 75
    if last_match_msg and last_match_msg.subtext.valence < -0.3: suggestions.tone = 20
    if last_match_msg and last_match_msg.wordCount < 10: suggestions.length = 30
    else: suggestions.length = 60
    if last_match_msg and last_match_msg.questionInfo.isQuestion:
        suggestions.endWithQuestion = False
    high_score_topics = [topic for topic, details in memory.topics.items() if details.score > 0.6]
    if high_score_topics:
        suggestions.keyTalkingPoints.append(f"Re-engage on a high-scoring topic like '{random.choice(high_score_topics)}'.")
    if memory.insideJokes:
        suggestions.keyTalkingPoints.append(f"Reference the inside joke about '{memory.insideJokes[-1]}'.")
    logger.debug(f"Response suggestions result: {suggestions.model_dump_json(indent=2)}")
    return suggestions

def _get_suggested_next_action(memory: MatchMemory, last_match_msg: Optional[MessageAnalysis]) -> str:
    logger.debug(f"Getting suggested next action. Rapport: {memory.rapportScore}, Investment: {memory.investmentScore}")
    if last_match_msg and any(re.search(p, last_match_msg.content.lower()) for p in SHIT_TEST_PATTERNS):
        logger.debug("Shit test detected. Suggesting: MAINTAIN_FRAME")
        return "MAINTAIN_FRAME"
    if memory.rapportScore > 0.7 and memory.investmentScore > 0.5:
        logger.debug("High rapport and investment. Suggesting: PROPOSE_DATE")
        return "PROPOSE_DATE"
    if memory.rapportScore > 0.5 and memory.investmentScore > 0.2:
        logger.debug("Good rapport and investment. Suggesting: ESCALATE_FLIRT")
        return "ESCALATE_FLIRT"
    logger.debug("Default suggestion: BUILD_RAPPORT")
    return "BUILD_RAPPORT"

def _detect_geo_related(doc: spacy.tokens.Doc) -> bool:
    logger.debug(f"Detecting geo-related terms in: '{doc.text}'")
    result = any(token.lemma_ in GEO_TRIGGERS for token in doc)
    logger.debug(f"Geo-related result: {result}")
    return result

def _suggest_response_style(analysis: MessageAnalysis) -> str:
    logger.debug(f"Suggesting response style for message: {analysis.model_dump_json()}")
    if analysis.subtext.isSarcastic:
        logger.debug("Sarcasm detected, suggesting witty style.")
        return "witty"
    if "flirting_or_sexual" in analysis.subtext.intents:
        logger.debug("Flirting intent detected, suggesting playful style.")
        return "playful"
    if analysis.subtext.isVulnerable: return "supportive"
    if analysis.questionInfo.isQuestion: return "direct"
    if analysis.subtext.valence > 0.5: return "charming"
    return "casual"

def _analyze_question(doc: spacy.tokens.Doc) -> QuestionInfo:
    logger.debug(f"Analyzing question for: '{doc.text}'")
    text_lower = doc.text.lower().strip()
    result = QuestionInfo()
    if text_lower.endswith('?'):
        result = QuestionInfo(isQuestion=True, count=1, type="open" if doc[0].tag_ in ("WP", "WRB") else "closed")
    elif any(text_lower.startswith(s) for s in INDIRECT_QUESTION_STARTERS):
        result = QuestionInfo(isQuestion=True, count=1, type="indirect")
    logger.debug(f"Question analysis result: {result.model_dump_json()}")
    return result

def _is_low_effort(text: str, doc: spacy.tokens.Doc) -> bool:
    logger.debug(f"Checking for low effort: '{text}'")
    text_clean = text.strip().lower()
    if len(doc) < 4 and text_clean in LOW_EFFORT_WORDS:
        logger.debug("Low effort detected (short message in low effort list).")
        return True
    result = all(w.strip(".,!?-") in LOW_EFFORT_WORDS for w in text_clean.split())
    logger.debug(f"Low effort result: {result}")
    return result

def _determine_conversation_state_and_pacing(history: List[ScrapedConversationMessage], last_match_analysis: Optional[MessageAnalysis]) -> Tuple[str, str]:
    logger.debug("Determining conversation state.")
    if not history:
        logger.debug("No history, conversation state is OPENER.")
        return "OPENER", "normal"

    last_message = history[-1]

    if last_message.role == 'user':
        return "AWAITING_REPLY", "normal"

    # If the last message is from the match (assistant)
    if last_message.date:
        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            last_message_date = datetime.datetime.fromisoformat(last_message.date.replace("Z", "+00:00"))
            time_since_last_message = now - last_message_date

            if time_since_last_message.total_seconds() < 24 * 3600:
                return "ACTIVE_CONVO", "normal"
            elif time_since_last_message.total_seconds() < 72 * 3600:
                return "STALLED", "slow"
            else:
                return "DEAD_CONVO", "stopped"
        except (ValueError, TypeError, AttributeError):
            # Fallback if date is invalid
            return "ACTIVE_CONVO", "normal"

    # Fallback if there's no date on the last message
    logger.debug("No date on last message, falling back to ACTIVE_CONVO.")
    return "ACTIVE_CONVO", "normal"

def _has_recent_greeting(history: List[ScrapedConversationMessage]) -> bool:
    logger.debug("Checking for recent greeting.")
    now = datetime.datetime.now(datetime.timezone.utc)
    for msg in reversed(history):
        try:
            msg_date = datetime.datetime.fromisoformat(msg.date.replace("Z", "+00:00"))
            if (now - msg_date).total_seconds() > 12 * 3600:
                logger.debug("No recent greeting found within the last 12 hours.")
                return False
            if msg.role == 'user' and any(greet in msg.content.lower() for greet in GREETING_KEYWORDS):
                logger.debug("Recent greeting found.")
                return True
        except (ValueError, TypeError, AttributeError, IndexError):
            continue
    logger.debug("No greeting found in recent history.")
    return False
