import logging
from typing import List

from analysis_models import SexualAnalysis, MessageAnalysis, MatchMemory, ConsentSignal
from constants import SEXUAL_WORDS

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
        sexual_analysis.sexualIntentConfidence = min(0.95, 0.5 + (match_sexual_intents * 0.1))
    if user_sexual_intents > 0:
        sexual_analysis.reciprocityScore = min(1.0, match_sexual_intents / user_sexual_intents)
    elif match_sexual_intents > 0:
        # User has not reciprocated, score is 0
        sexual_analysis.reciprocityScore = 0.0
    else:
        # No sexual intents from either side, reciprocity is balanced
        sexual_analysis.reciprocityScore = 1.0
    if sexual_analysis.sexualTensionScore > 0.7:
        sexual_analysis.escalationPace = "fast"
    elif sexual_analysis.sexualTensionScore > 0.4:
        sexual_analysis.escalationPace = "moderate"
    else:
        sexual_analysis.escalationPace = "slow"
    sexual_analysis.sexualCommunicationStyle = "direct_and_explicit" if any(w in " ".join(m.content for m in analyzed_messages) for w in SEXUAL_WORDS) else "implicit"
    logger.debug(f"Sexual analysis result: {sexual_analysis.model_dump_json(indent=2)}")
    return sexual_analysis
