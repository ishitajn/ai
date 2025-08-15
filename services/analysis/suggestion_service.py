import logging
import random
import re
from typing import Optional

from analysis_models import ResponseSuggestions, FullConversationAnalysis, MatchMemory, MessageAnalysis
from constants import SHIT_TEST_PATTERNS

logger = logging.getLogger(__name__)

def get_response_suggestions(analysis: FullConversationAnalysis) -> ResponseSuggestions:
    logger.debug("Getting response suggestions.")
    suggestions = ResponseSuggestions()
    memory = analysis.memory
    last_match_msg = analysis.lastMessageAnalysis
    suggestions.suggestedNextAction = _get_suggested_next_action(memory, last_match_msg)
    if memory.dateArcPhase == "escalation":
        suggestions.tone = 75
    if last_match_msg and last_match_msg.subtext.valence < -0.3:
        suggestions.tone = 20
    if last_match_msg and last_match_msg.wordCount < 10:
        suggestions.length = 30
    else:
        suggestions.length = 60
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
