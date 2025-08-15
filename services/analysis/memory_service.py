import logging
import spacy
from typing import List
from spacy.matcher.dependencymatcher import defaultdict
from transformers import pipeline

from analysis_models import (
    MessageAnalysis, MatchMemory, PersonalityProfile, TopicDetails
)
from utils.constants import RED_FLAGS

logger = logging.getLogger(__name__)

def update_memory_from_history(
    history: List,
    analyzed_messages: List[MessageAnalysis],
    nlp: spacy.language.Language,
    topic_classifier: pipeline
) -> MatchMemory:
    memory = MatchMemory()
    topic_sentiments = defaultdict(list)
    user_messages = [m for m in analyzed_messages if m.role == 'user']
    match_messages = [m for m in analyzed_messages if m.role == 'assistant']

    investment_delta = 0
    if match_messages and user_messages:
        last_match_msg, last_user_msg = match_messages[-1], user_messages[-1]
        if last_match_msg.questionInfo.isQuestion:
            investment_delta += 0.2
        if last_user_msg.questionInfo.isQuestion and not last_match_msg.questionInfo.isQuestion:
            investment_delta -= 0.15
        if last_match_msg.wordCount >= last_user_msg.wordCount * 0.8:
            investment_delta += 0.1
        else:
            investment_delta -= 0.1
        if last_match_msg.isLowEffort:
            investment_delta -= 0.3
    logger.debug(f"Calculated investment delta: {investment_delta}")
    memory.investmentScore = max(-1, min(1, (memory.investmentScore * 0.8) + investment_delta))
    logger.debug(f"Updated investment score: {memory.investmentScore}")

    total_valence, tension_delta = 0, 0
    for msg in analyzed_messages:
        if msg.role == 'assistant':
            total_valence += msg.subtext.valence
        if "flirting_or_sexual" in msg.subtext.intents:
            tension_delta += 0.3
    if user_messages and match_messages and \
       "flirting_or_sexual" in user_messages[-1].subtext.intents and \
       match_messages[-1].subtext.valence < -0.2:
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
        memory.personalityProfile = _get_personality_profile(match_messages_text, topic_classifier)

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

    memory.dateArcPhase = "rapport"  # Simplified
    logger.debug(f"Final memory object: {memory.model_dump_json(indent=2)}")
    return memory

def _get_personality_profile(text: str, topic_classifier: pipeline) -> PersonalityProfile:
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
