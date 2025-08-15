import logging
import random
import re
from typing import Optional

from analysis_models import ResponseSuggestions, FullConversationAnalysis, MatchMemory, MessageAnalysis
from constants import (
    SHIT_TEST_PATTERNS, SUGGESTION_TONE_ESCALATION, SUGGESTION_TONE_NEGATIVE_REPLY,
    SUGGESTION_TONE_VALENCE_THRESHOLD, SUGGESTION_LENGTH_SHORT_THRESHOLD,
    SUGGESTION_LENGTH_SHORT, SUGGESTION_LENGTH_NORMAL, SUGGESTION_HIGH_SCORE_TOPIC_THRESHOLD,
    SUGGESTION_ACTION_PROPOSE_DATE_RAPPORT, SUGGESTION_ACTION_PROPOSE_DATE_INVESTMENT,
    SUGGESTION_ACTION_ESCALATE_FLIRT_RAPPORT, SUGGESTION_ACTION_ESCALATE_FLIRT_INVESTMENT
)

logger = logging.getLogger(__name__)

def get_response_suggestions(analysis: FullConversationAnalysis) -> ResponseSuggestions:
    logger.debug("Getting response suggestions.")
    suggestions = ResponseSuggestions()
    memory = analysis.memory
    last_match_msg = analysis.lastMessageAnalysis
    suggestions.suggestedNextAction = _get_suggested_next_action(memory, last_match_msg)
    if memory.dateArcPhase == "escalation":
        suggestions.tone = SUGGESTION_TONE_ESCALATION
    if last_match_msg and last_match_msg.subtext.valence < SUGGESTION_TONE_VALENCE_THRESHOLD:
        suggestions.tone = SUGGESTION_TONE_NEGATIVE_REPLY
    if last_match_msg and last_match_msg.wordCount < SUGGESTION_LENGTH_SHORT_THRESHOLD:
        suggestions.length = SUGGESTION_LENGTH_SHORT
    else:
        suggestions.length = SUGGESTION_LENGTH_NORMAL
    if last_match_msg and last_match_msg.questionInfo.isQuestion:
        suggestions.endWithQuestion = False
    high_score_topics = [topic for topic, details in memory.topics.items() if details.score > SUGGESTION_HIGH_SCORE_TOPIC_THRESHOLD]
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
    if memory.rapportScore > SUGGESTION_ACTION_PROPOSE_DATE_RAPPORT and memory.investmentScore > SUGGESTION_ACTION_PROPOSE_DATE_INVESTMENT:
        logger.debug("High rapport and investment. Suggesting: PROPOSE_DATE")
        return "PROPOSE_DATE"
    if memory.rapportScore > SUGGESTION_ACTION_ESCALATE_FLIRT_RAPPORT and memory.investmentScore > SUGGESTION_ACTION_ESCALATE_FLIRT_INVESTMENT:
        logger.debug("Good rapport and investment. Suggesting: ESCALATE_FLIRT")
        return "ESCALATE_FLIRT"
    logger.debug("Default suggestion: BUILD_RAPPORT")
    return "BUILD_RAPPORT"
