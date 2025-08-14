import spacy
import datetime
import random
import re
from typing import List, Dict, Tuple, Optional

from spacy.matcher.dependencymatcher import defaultdict
from sqlalchemy.orm import Session

from api_models import ScrapedData, FullUISettings, InitialUISettings, ScrapedConversationMessage
from analysis_models import (
    MessageAnalysis, SubtextAnalysis, QuestionInfo, FullConversationAnalysis, 
    MatchMemory, TopicDetails, StrategicGoal
)
from utils.constants import (
    POSITIVE_WORDS, NEGATIVE_WORDS, AROUSAL_WORDS, VULNERABLE_WORDS,
    SEXUAL_WORDS, SEXUAL_EMOJIS, LOW_EFFORT_WORDS, GREETING_KEYWORDS,
    GEO_TRIGGERS, AMBIGUOUS_PHRASES, SARCASTIC_MARKERS, INTENSIFIERS,
    NEGATION_WORDS, INDIRECT_QUESTION_STARTERS, PLANNING_WORDS, POWER_MOVE_PHRASES,
    PROFESSIONAL_WORDS, SHIT_TEST_PATTERNS
)
from db import crud
from config import *
from services.geo_service import update_geo_context

# --- Initialization ---
try:
    nlp = spacy.load(SPACY_MODEL)
except OSError:
    print(f"Downloading '{SPACY_MODEL}' model for spaCy...")
    from spacy.cli import download
    download(SPACY_MODEL)
    nlp = spacy.load(SPACY_MODEL)

# --- Main Service Functions ---

def run_full_conversation_analysis(db: Session, match_id: str, scraped_data: ScrapedData, ui_settings: InitialUISettings) -> FullConversationAnalysis:
    """
    The main entry point for a new analysis request. It orchestrates all sub-modules,
    builds a complete analysis object from scratch, and saves it to the database.
    """
    analyzed_messages = [analyze_single_message(msg.content, msg.role) for msg in scraped_data.conversationHistory]
    user_messages = [m for m in analyzed_messages if m.role == 'user']
    match_messages = [m for m in analyzed_messages if m.role == 'assistant']

    memory = MatchMemory()
    memory = _update_memory_from_history(user_messages, match_messages, memory)
    
    match_profile_doc = nlp(scraped_data.theirProfile)
    update_geo_context(memory, ui_settings.myLocation, scraped_data.theirLocationString, match_profile_doc)

    last_match_msg = match_messages[-1] if match_messages else None
    state, pacing = _determine_conversation_state_and_pacing(scraped_data.conversationHistory, last_match_msg)
    
    # Note: When running a fresh analysis, we don't have FullUISettings yet,
    # so we create a temporary one to pass to the goal determination.
    # The initial goal will therefore always be based on the "Balanced" strategy.
    temp_ui_settings = FullUISettings(**ui_settings.model_dump())
    strategic_goal = _determine_strategic_goal(memory, last_match_msg, temp_ui_settings)

    analysis = FullConversationAnalysis(
        conversationState=state,
        conversationPacing=pacing,
        current_topic=last_match_msg.topics[0] if last_match_msg and last_match_msg.topics else None,
        lastUserMessageAnalysis=user_messages[-1] if user_messages else None,
        lastMatchMessageAnalysis=last_match_msg,
        suppressGreeting=_has_recent_greeting(scraped_data.conversationHistory),
        strategicGoal=strategic_goal,
        memory=memory,
    )

    crud.save_match_analysis(db, match_id, analysis)
    return analysis

def load_and_apply_overrides(db: Session, match_id: str, ui_settings: FullUISettings) -> FullConversationAnalysis:
    """
    Loads the latest analysis from the DB and applies user overrides before regeneration.
    """
    analysis = crud.get_match_analysis(db, match_id)
    if not analysis:
        raise ValueError(f"No analysis found for matchId {match_id}. Please run /analyze first.")

    if ui_settings.investmentScore_override is not None: analysis.memory.investmentScore = ui_settings.investmentScore_override
    if ui_settings.rapportScore_override is not None: analysis.memory.rapportScore = ui_settings.rapportScore_override
    if ui_settings.sexualTension_override is not None: analysis.memory.sexualTension = ui_settings.sexualTension_override
    if ui_settings.isLongDistance_override is not None: analysis.memory.isLongDistance = ui_settings.isLongDistance_override
    if ui_settings.engagementState_override is not None: analysis.memory.engagementState = ui_settings.engagementState_override
    if ui_settings.dateArcPhase_override is not None: analysis.memory.dateArcPhase = ui_settings.dateArcPhase_override

    if ui_settings.overrideGoal:
        analysis.strategicGoal = StrategicGoal(
            type=ui_settings.overrideGoal,
            justification="User has manually selected this goal, overriding the AI's initial analysis.",
            urgency="high"
        )
    else:
        analysis.strategicGoal = _determine_strategic_goal(
            analysis.memory, analysis.lastMatchMessageAnalysis, ui_settings
        )
    return analysis

def get_initial_ui_settings(analysis: FullConversationAnalysis, initial_settings: InitialUISettings) -> FullUISettings:
    """Calculates smart defaults for the UI based on the initial analysis."""
    defaults = {
        'flirtyValue': DEFAULT_FLIRTY_VALUE, 'lengthValue': DEFAULT_LENGTH_VALUE,
        'linguisticStyle': DEFAULT_LINGUISTIC_STYLE, 'humorStyle': DEFAULT_HUMOR_STYLE,
        'vulnerabilityLevel': DEFAULT_VULNERABILITY_LEVEL, 'endWithQuestion': DEFAULT_END_WITH_QUESTION,
        'persona': DEFAULT_PERSONA, 'ultimateGoal': DEFAULT_ULTIMATE_GOAL
    }
    mem = analysis.memory
    last_match = analysis.lastMatchMessageAnalysis

    if mem.dateArcPhase == "escalation": defaults['flirtyValue'] = 75
    if last_match and last_match.subtext.valence < -0.3: defaults['flirtyValue'] = 20
    if last_match and last_match.questionInfo.isQuestion: defaults['endWithQuestion'] = False
    if analysis.conversationPacing == "stalled": defaults['endWithQuestion'] = True
    if last_match and last_match.wordCount < 10: defaults['lengthValue'] = 30

    final_settings = FullUISettings(**initial_settings.model_dump(), **defaults)
    return final_settings

# --- Helper Functions for Analysis ---

def analyze_single_message(text: str, role: str) -> MessageAnalysis:
    if not text: return MessageAnalysis(content="", role=role, subtext=SubtextAnalysis(), questionInfo=QuestionInfo())
    doc = nlp(text)
    return MessageAnalysis(
        content=text, role=role, subtext=_analyze_subtext(doc),
        questionInfo=_analyze_question(doc), topics=_extract_topics_and_entities(doc)[0],
        keyEntities=_extract_topics_and_entities(doc)[1], isLowEffort=_is_low_effort(text, doc),
        wordCount=len([token for token in doc if token.is_alpha]),
    )

def _analyze_subtext(doc: spacy.tokens.Doc) -> SubtextAnalysis:
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
        valence = max(valence, 0.5); arousal += 0.7
    if any(p in text_lower for p in VULNERABLE_WORDS): subtext.isVulnerable = True
    if any(m in text_lower for m in SARCASTIC_MARKERS) and valence > 0: subtext.isSarcastic = True; valence *= -0.5
    subtext.valence = max(-1, min(1, valence)); subtext.arousal = max(-1, min(1, arousal))
    subtext.intents = list(set(subtext.intents))
    return subtext

def _analyze_question(doc: spacy.tokens.Doc) -> QuestionInfo:
    text_lower = doc.text.lower().strip()
    if text_lower.endswith('?'): return QuestionInfo(isQuestion=True, count=1, type="open" if doc[0].tag_ in ("WP", "WRB") else "closed")
    if any(text_lower.startswith(s) for s in INDIRECT_QUESTION_STARTERS): return QuestionInfo(isQuestion=True, count=1, type="indirect")
    return QuestionInfo()

def _extract_topics_and_entities(doc: spacy.tokens.Doc) -> Tuple[List[str], Dict[str, List[str]]]:
    topics = [c.text.lower() for c in doc.noun_chunks if len(c.text.split()) > 1 and not c.root.is_stop]
    entities = defaultdict(list)
    for ent in doc.ents: entities[ent.label_].append(ent.text)
    return list(set(topics)), dict(entities)

def _is_low_effort(text: str, doc: spacy.tokens.Doc) -> bool:
    text_clean = text.strip().lower()
    if len(doc) < 4 and text_clean in LOW_EFFORT_WORDS: return True
    return all(w.strip(".,!?-") in LOW_EFFORT_WORDS for w in text_clean.split())

def _detect_shit_test(text: str) -> bool:
    return any(re.search(p, text.lower()) for p in SHIT_TEST_PATTERNS)

def _determine_conversation_state_and_pacing(history: List[ScrapedConversationMessage], last_match_analysis: Optional[MessageAnalysis]) -> Tuple[str, str]:
    if not history: return "OPENER", "normal"
    last_message, pacing = history[-1], "normal"
    if last_message.date:
        try:
            last_date = datetime.datetime.fromisoformat(last_message.date.replace("Z", "+00:00"))
            time_since = (datetime.datetime.now(datetime.timezone.utc) - last_date).total_seconds() / 3600
            if time_since < 1: pacing = "fast"
            elif time_since > 48: pacing = "stalled"
        except (ValueError, TypeError): pass
    if last_message.role == "user": return "AWAITING_REPLY", pacing
    return "EARLY_CONVO" if sum(1 for m in history if m.role == 'assistant') < 4 else "ACTIVE_CONVO", pacing

def _has_recent_greeting(history: List[ScrapedConversationMessage]) -> bool:
    now = datetime.datetime.now(datetime.timezone.utc)
    for msg in reversed(history):
        try:
            msg_date = datetime.datetime.fromisoformat(msg.date.replace("Z", "+00:00"))
            if (now - msg_date).total_seconds() > 12 * 3600: break
            if msg.role == 'user' and msg.content.lower().split()[0].strip(".,!?-") in GREETING_KEYWORDS: return True
        except (ValueError, TypeError, AttributeError, IndexError): continue
    return False

def _update_memory_from_history(user_messages: List[MessageAnalysis], match_messages: List[MessageAnalysis], memory: MatchMemory) -> MatchMemory:
    investment_delta = 0
    if match_messages and user_messages:
        last_match_msg, last_user_msg = match_messages[-1], user_messages[-1]
        if last_match_msg.questionInfo.isQuestion: investment_delta += INVESTMENT_SCORE_QUESTION_ASKED_BONUS
        if last_user_msg.questionInfo.isQuestion and not last_match_msg.questionInfo.isQuestion: investment_delta -= INVESTMENT_SCORE_QUESTION_IGNORED_PENALTY
        if last_match_msg.wordCount >= last_user_msg.wordCount * 0.8: investment_delta += INVESTMENT_SCORE_LENGTH_MATCH_BONUS
        else: investment_delta -= INVESTMENT_SCORE_LENGTH_MISMATCH_PENALTY
        if last_match_msg.isLowEffort: investment_delta -= INVESTMENT_SCORE_LOW_EFFORT_PENALTY
    memory.investmentScore = max(-1, min(1, (memory.investmentScore * INVESTMENT_SCORE_DECAY_FACTOR) + investment_delta))

    total_valence, tension_delta = 0, 0
    for msg in match_messages:
        total_valence += msg.subtext.valence
        if "flirting_or_sexual" in msg.subtext.intents: tension_delta += SEXUAL_TENSION_INTENT_BONUS
    if user_messages and match_messages and "flirting_or_sexual" in user_messages[-1].subtext.intents and match_messages[-1].subtext.valence < -0.2:
        tension_delta -= SEXUAL_TENSION_NEGATIVE_REACTION_PENALTY
    memory.sexualTension = max(0, min(1, (memory.sexualTension * SEXUAL_TENSION_DECAY_FACTOR) + tension_delta))
    
    avg_valence = total_valence / len(match_messages) if match_messages else 0
    rapport_bonus = min(len(match_messages) / RAPPORT_CONVO_LENGTH_FACTOR, RAPPORT_CONVO_LENGTH_BONUS_MAX)
    memory.rapportScore = max(0, min(1, (avg_valence + 1) / 2 + rapport_bonus))

    all_messages = sorted(user_messages + match_messages, key=lambda m: m.content)
    for msg in all_messages:
        message_doc = nlp(msg.content)
        for topic_text in msg.topics:
            if topic_text not in memory.topics: memory.topics[topic_text] = TopicDetails()
            details = memory.topics[topic_text]
            details.mentions += 1; details.sentiment_sum += msg.subtext.valence
            details.category = _categorize_topic(topic_text, message_doc)
    for topic, details in memory.topics.items():
        if details.mentions > 0: details.avg_sentiment = details.sentiment_sum / details.mentions
        if details.avg_sentiment > TOPIC_STATUS_KEEP_THRESHOLD: details.status = "keep"
        elif details.avg_sentiment < TOPIC_STATUS_AVOID_THRESHOLD: details.status = "avoid"
        else: details.status = "neutral"
    return memory

def _categorize_topic(topic_text: str, message_doc: spacy.tokens.Doc) -> str:
    msg_text_lower = message_doc.text.lower()
    if any(w in msg_text_lower for w in SEXUAL_WORDS): return "sexual"
    if any(w in msg_text_lower for w in PLANNING_WORDS): return "planning"
    if any(w in msg_text_lower for w in VULNERABLE_WORDS): return "vulnerable"
    if any(w in msg_text_lower for w in PROFESSIONAL_WORDS): return "professional"
    if any(token.lemma_ in GEO_TRIGGERS for token in message_doc): return "geo-context"
    return "general_interest"

STRATEGY_THRESHOLDS = {
    "Patient": {
        "ask_rapport": 0.8,
        "ask_investment": 0.7,
        "ask_sexual_tension": 0.75,
        "escalate_rapport": 0.6,
        "escalate_investment": 0.4,
        "push_pull_probability": 0.15,
    },
    "Balanced": {
        "ask_rapport": ASK_RAPPORT_THRESHOLD,
        "ask_investment": ASK_INVESTMENT_THRESHOLD,
        "ask_sexual_tension": ASK_SEXUAL_TENSION_THRESHOLD,
        "escalate_rapport": ESCALATE_RAPPORT_THRESHOLD,
        "escalate_investment": ESCALATE_INVESTMENT_THRESHOLD,
        "push_pull_probability": PUSH_PULL_TRIGGER_PROBABILITY,
    },
    "Aggressive": {
        "ask_rapport": 0.6,
        "ask_investment": 0.4,
        "ask_sexual_tension": 0.5,
        "escalate_rapport": 0.4,
        "escalate_investment": 0.15,
        "push_pull_probability": 0.35,
    }
}

def _get_strategy_thresholds(strategy_mode: str) -> dict:
    """Returns a dictionary of thresholds based on the selected strategy mode."""
    return STRATEGY_THRESHOLDS.get(strategy_mode, STRATEGY_THRESHOLDS["Balanced"])


def _determine_strategic_goal(memory: MatchMemory, last_match_msg: Optional[MessageAnalysis], ui_settings: FullUISettings) -> StrategicGoal:
    """Determines the next strategic goal based on memory, context, and the selected strategy mode."""
    thresholds = _get_strategy_thresholds(ui_settings.strategyMode)
    ultimate_goal = ui_settings.ultimateGoal

    if memory.investmentScore < DORMANT_INVESTMENT_THRESHOLD:
        memory.engagementState = "DORMANT"
    elif DORMANT_INVESTMENT_THRESHOLD <= memory.investmentScore < LUKEWARM_INVESTMENT_THRESHOLD:
        memory.engagementState = "LUKEWARM"
    else:
        memory.engagementState = "ACTIVE"

    if last_match_msg and _detect_shit_test(last_match_msg.content):
        return StrategicGoal(type="MAINTAIN_FRAME", justification="A 'shit test' was detected. Respond with non-defensive humor and confidence.", urgency="critical")
    if memory.engagementState == "DORMANT":
        return StrategicGoal(type="PROVIDE_STIMULUS", justification="They are unresponsive. Broadcast value with zero expectation of a reply.", urgency="low")
    if memory.engagementState == "LUKEWARM":
        return StrategicGoal(type="ENCOURAGE_INTERACTION", justification="They are giving minimal responses. Make it easy for them to give a better answer.", urgency="normal")
    if memory.dateArcPhase == "planning":
        return StrategicGoal(type="HANDLE_LOGISTICS", justification="A date is being planned. Focus on confirming details.", urgency="high")

    ask_conditions_met = memory.rapportScore > thresholds['ask_rapport'] and memory.investmentScore > thresholds['ask_investment']
    if ask_conditions_met:
        if ultimate_goal == "Sexual_Encounter":
            if memory.sexualTension > thresholds['ask_sexual_tension']:
                return StrategicGoal(type="PROPOSE_ENCOUNTER", justification="Sexual tension and investment are very high. Propose an encounter.", urgency="high")
            else:
                return StrategicGoal(type="ESCALATE_SEXUAL_TENSION", justification="Investment is high, but sexual tension is not yet sufficient. Escalate.", urgency="normal")
        else:
            if memory.isLongDistance:
                return StrategicGoal(type="PROPOSE_VIRTUAL_DATE", justification="Rapport and investment are high, but they are long distance. Propose a video call.", urgency="high")
            else:
                return StrategicGoal(type="PROPOSE_DATE", justification="Rapport and investment are high and they are local. Ask for an in-person date.", urgency="high")

    escalate_conditions_met = memory.rapportScore > thresholds['escalate_rapport'] and memory.investmentScore > thresholds['escalate_investment']
    if escalate_conditions_met:
        if random.random() < thresholds['push_pull_probability']:
            return StrategicGoal(type="APPLY_PUSH_PULL", justification="The conversation is good but safe. Create a spark by mixing a compliment with a playful challenge.", urgency="normal")

        memory.dateArcPhase = "escalation"
        return StrategicGoal(type="ESCALATE_FLIRT", justification="Rapport is good and they are invested. Time to move from friendly to flirty.", urgency="normal")

    return StrategicGoal(type="BUILD_RAPPORT", justification="The conversation is active. Continue building connection and positive sentiment.", urgency="normal")