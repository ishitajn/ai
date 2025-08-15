import logging
from typing import List, Optional

import spacy
from spacy.matcher.dependencymatcher import defaultdict
from transformers import pipeline, Pipeline

from analysis_models import (MatchMemory, MessageAnalysis, PersonalityProfile, TopicDetails)
from constants import (
    RED_FLAGS, PLANNING_WORDS, INVESTMENT_QUESTION_BONUS, INVESTMENT_QUESTION_PENALTY,
    INVESTMENT_WORD_COUNT_RATIO, INVESTMENT_WORD_COUNT_BONUS, INVESTMENT_LOW_EFFORT_PENALTY,
    INVESTMENT_SCORE_DECAY, SEXUAL_TENSION_FLIRT_BONUS, SEXUAL_TENSION_NEG_VALENCE_THRESHOLD,
    SEXUAL_TENSION_REJECTION_PENALTY, SEXUAL_TENSION_DECAY, RAPPORT_MSG_COUNT_THRESHOLD,
    RAPPORT_MSG_COUNT_MAX_BONUS, RAPPORT_VALENCE_DIVISOR, INSIDE_JOKE_VALENCE_THRESHOLD,
    TOPIC_MENTION_BONUS_FACTOR, TOPIC_MENTION_MAX_BONUS, ESCALATION_SEXUAL_TENSION_THRESHOLD,
    ESCALATION_INVESTMENT_THRESHOLD, PLANNING_RECENT_MESSAGE_COUNT
)

logger = logging.getLogger(__name__)


def update_memory_from_history(
        history: List,
        analyzed_messages: List[MessageAnalysis],
        nlp: spacy.language.Language,
        topic_classifier: Pipeline
) -> MatchMemory:
    memory = MatchMemory()
    topic_sentiments = defaultdict(list)
    user_messages = [m for m in analyzed_messages if m.role == 'user']
    match_messages = [m for m in analyzed_messages if m.role == 'assistant']

    investment_delta = 0
    if match_messages and user_messages:
        last_match_msg, last_user_msg = match_messages[-1], user_messages[-1]
        if last_match_msg.questionInfo.isQuestion:
            investment_delta += INVESTMENT_QUESTION_BONUS
        if last_user_msg.questionInfo.isQuestion and not last_match_msg.questionInfo.isQuestion:
            investment_delta -= INVESTMENT_QUESTION_PENALTY
        if last_match_msg.wordCount >= last_user_msg.wordCount * INVESTMENT_WORD_COUNT_RATIO:
            investment_delta += INVESTMENT_WORD_COUNT_BONUS
        else:
            investment_delta -= INVESTMENT_WORD_COUNT_BONUS
        if last_match_msg.isLowEffort:
            investment_delta -= INVESTMENT_LOW_EFFORT_PENALTY
    logger.debug(f"Calculated investment delta: {investment_delta}")
    memory.investmentScore = max(-1, min(1, (memory.investmentScore * INVESTMENT_SCORE_DECAY) + investment_delta))
    logger.debug(f"Updated investment score: {memory.investmentScore}")

    total_valence, tension_delta = 0, 0
    for msg in analyzed_messages:
        if msg.role == 'assistant':
            total_valence += msg.subtext.valence
        if "flirting_or_sexual" in msg.subtext.intents:
            tension_delta += SEXUAL_TENSION_FLIRT_BONUS
    if user_messages and match_messages and "flirting_or_sexual" in user_messages[-1].subtext.intents and match_messages[-1].subtext.valence < SEXUAL_TENSION_NEG_VALENCE_THRESHOLD:
        tension_delta -= SEXUAL_TENSION_REJECTION_PENALTY
    logger.debug(f"Calculated sexual tension delta: {tension_delta}")
    memory.sexualTension = max(0, min(1, (memory.sexualTension * SEXUAL_TENSION_DECAY) + tension_delta))
    logger.debug(f"Updated sexual tension: {memory.sexualTension}")

    avg_valence = total_valence / len(match_messages) if match_messages else 0
    rapport_bonus = min(len(match_messages) / RAPPORT_MSG_COUNT_THRESHOLD, RAPPORT_MSG_COUNT_MAX_BONUS)
    memory.rapportScore = max(0, min(1, (avg_valence + 1) / RAPPORT_VALENCE_DIVISOR + rapport_bonus))
    logger.debug(f"Calculated rapport score: {memory.rapportScore} (avg_valence: {avg_valence}, bonus: {rapport_bonus})")

    match_messages_text = " ".join([msg.content for msg in match_messages])
    if topic_classifier and match_messages_text:
        memory.personalityProfile = _get_personality_profile(match_messages_text, topic_classifier)

    memory.redFlags = _detect_red_flags(analyzed_messages)

    for i, msg in enumerate(analyzed_messages):
        if msg.questionInfo.isQuestion:
            memory.questionHistory.append(msg.content)
        if msg.role == 'assistant' and msg.subtext.valence > INSIDE_JOKE_VALENCE_THRESHOLD and any(laugh in msg.content.lower() for laugh in ["lmao", "lol", "haha"]):
            if i > 0 and history[i-1].role == 'user':
                joke_subject = _extract_joke_subject(history[i-1].content, nlp)
                if joke_subject:
                    memory.insideJokes.append(joke_subject)
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
        mention_bonus = min(memory.topics[topic].mentions * TOPIC_MENTION_BONUS_FACTOR, TOPIC_MENTION_MAX_BONUS)
        memory.topics[topic].score = max(-1, min(1, avg_sentiment + mention_bonus))

    # Determine the date arc phase
    phase = "rapport"
    if memory.sexualTension > ESCALATION_SEXUAL_TENSION_THRESHOLD or memory.investmentScore > ESCALATION_INVESTMENT_THRESHOLD:
        phase = "escalation"

    # Check last 4 messages for planning words
    recent_messages_text = " ".join(msg.content.lower() for msg in analyzed_messages[-PLANNING_RECENT_MESSAGE_COUNT:])
    if any(word in recent_messages_text for word in PLANNING_WORDS):
        phase = "planning"

    memory.dateArcPhase = phase
    logger.debug(f"Final memory object: {memory.model_dump_json(indent=2)}")
    return memory


def _extract_joke_subject(text: str, nlp: spacy.language.Language) -> Optional[str]:
    """Extracts the most likely subject of a joke from a sentence."""
    doc = nlp(text)
    # Find the longest noun chunk that is not a pronoun
    longest_noun_chunk = ""
    for chunk in doc.noun_chunks:
        if chunk.root.pos_ != "PRON" and len(chunk.text) > len(longest_noun_chunk):
            longest_noun_chunk = chunk.text
    return longest_noun_chunk if longest_noun_chunk else None


def _get_personality_profile(text: str, topic_classifier: pipeline) -> PersonalityProfile:
    logger.debug(f"Getting personality profile for text: '{text[:100]}...'")
    profile = PersonalityProfile()
    if not topic_classifier:
        logger.debug("Topic classifier not available, returning empty profile.")
        return profile
    trait_labels = {
        "extraversion" : "extroverted, outgoing, and sociable language",
        "agreeableness": "agreeable, compassionate, and friendly language",
        "openness"     : "language showing openness, imagination, and curiosity"
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
