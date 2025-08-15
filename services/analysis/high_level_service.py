import logging
import datetime
from typing import List, Tuple, Optional

from api_models import ScrapedConversationMessage
from analysis_models import MessageAnalysis
from utils.constants import GREETING_KEYWORDS

logger = logging.getLogger(__name__)

def determine_conversation_state_and_pacing(
    history: List[ScrapedConversationMessage],
    last_match_analysis: Optional[MessageAnalysis]
) -> Tuple[str, str]:
    logger.debug("Determining conversation state.")
    if not history:
        logger.debug("No history, conversation state is OPENER.")
        return "OPENER", "normal"

    last_message = history[-1]

    if last_message.role == 'user':
        return "AWAITING_REPLY", "normal"

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
            return "ACTIVE_CONVO", "normal"

    logger.debug("No date on last message, falling back to ACTIVE_CONVO.")
    return "ACTIVE_CONVO", "normal"

def has_recent_greeting(history: List[ScrapedConversationMessage]) -> bool:
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
