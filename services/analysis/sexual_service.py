import logging
from typing import List

from analysis_models import SexualAnalysis, MessageAnalysis, MatchMemory, ConsentSignal
from constants import (
    SEXUAL_WORDS, SEXUAL_INTENT_CONFIDENCE_MAX, SEXUAL_INTENT_CONFIDENCE_BASE,
    SEXUAL_INTENT_CONFIDENCE_BONUS, RECIPROCITY_SCORE_MAX, RECIPROCITY_SCORE_UNRECIPROCATED,
    RECIPROCITY_SCORE_BALANCED, ESCALATION_PACE_FAST_THRESHOLD, ESCALATION_PACE_MODERATE_THRESHOLD,
    KINKS_AND_FETISHES_KEYWORDS
)

logger = logging.getLogger(__name__)

def get_sexual_analysis(analyzed_messages: List[MessageAnalysis], memory: MatchMemory) -> SexualAnalysis:
    logger.debug("Getting sexual analysis.")
    sexual_analysis = SexualAnalysis()
    sexual_analysis.sexualTensionScore = memory.sexualTension
    match_sexual_intents = sum(1 for msg in analyzed_messages if msg.role == 'assistant' and "flirting_or_sexual" in msg.subtext.intents)
    user_sexual_intents = sum(1 for msg in analyzed_messages if msg.role == 'user' and "flirting_or_sexual" in msg.subtext.intents)
    for msg in analyzed_messages:
        if msg.role == 'assistant' and "can't wait" in msg.content.lower():
            sexual_analysis.consentSignals.append(ConsentSignal(type="enthusiastic_consent", evidence=msg.content))
    if match_sexual_intents > 0:
        sexual_analysis.sexualIntentConfidence = min(
            SEXUAL_INTENT_CONFIDENCE_MAX,
            SEXUAL_INTENT_CONFIDENCE_BASE + (match_sexual_intents * SEXUAL_INTENT_CONFIDENCE_BONUS)
        )
    if user_sexual_intents > 0:
        sexual_analysis.reciprocityScore = min(RECIPROCITY_SCORE_MAX, match_sexual_intents / user_sexual_intents)
    elif match_sexual_intents > 0:
        sexual_analysis.reciprocityScore = RECIPROCITY_SCORE_UNRECIPROCATED
    else:
        sexual_analysis.reciprocityScore = RECIPROCITY_SCORE_BALANCED
    if sexual_analysis.sexualTensionScore > ESCALATION_PACE_FAST_THRESHOLD:
        sexual_analysis.escalationPace = "fast"
    elif sexual_analysis.sexualTensionScore > ESCALATION_PACE_MODERATE_THRESHOLD:
        sexual_analysis.escalationPace = "moderate"
    else:
        sexual_analysis.escalationPace = "slow"
    sexual_analysis.sexualCommunicationStyle = "direct_and_explicit" if any(w in " ".join(m.content for m in analyzed_messages) for w in SEXUAL_WORDS) else "implicit"

    # Detect kinks and fetishes
    conversation_text = " ".join(msg.content.lower() for msg in analyzed_messages)
    found_kinks = {keyword for keyword in KINKS_AND_FETISHES_KEYWORDS if keyword in conversation_text}
    sexual_analysis.kinksAndFetishes = list(found_kinks)

    logger.debug(f"Sexual analysis result: {sexual_analysis.model_dump_json(indent=2)}")
    return sexual_analysis
