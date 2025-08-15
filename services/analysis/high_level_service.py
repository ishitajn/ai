import logging
import datetime
from typing import List, Tuple, Optional

from api_models import ScrapedConversationMessage
from analysis_models import MessageAnalysis
from constants import GREETING_KEYWORDS

logger = logging.getLogger(__name__)

TWO_DAYS = 24 * 2 * 3600
ONE_WEEK = 24 * 7 * 3600
ONE_MONTH = 24 * 30 * 3600


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

            seconds_since = time_since_last_message.total_seconds()

            if seconds_since < TWO_DAYS:
                if len(history) < 7:
                    return "EARLY_CONVO", "normal"
                return "ACTIVE_CONVO", "normal"
            # Order checks from longest to shortest time
            elif seconds_since >= ONE_MONTH:
                return "REENGAGING_MONTH", "normal"
            elif seconds_since >= ONE_WEEK:
                return "REENGAGING_WEEK", "normal"
            elif seconds_since >= TWO_DAYS:
                return "REENGAGING_DAY", "normal"
            else:
                # This case should logically not be reached, but as a fallback:
                return "DEAD_CONVO", "stopped"
        except (ValueError, TypeError, AttributeError):
            return "ACTIVE_CONVO", "normal"
    logger.debug("No date on last message, falling back to ACTIVE_CONVO.")
    return "ACTIVE_CONVO", "normal"

def has_recent_greeting(history: List[ScrapedConversationMessage]) -> bool:
    logger.debug("Checking for recent greeting.")
    # Ensure two_days_ago is timezone-aware (UTC)
    two_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=2)

    for msg in history:
        # Ensure message is from user and has a date
        if msg.role != "user" or not msg.date:
            continue

        try:
            # Ensure the parsed date is timezone-aware
            msg_time = datetime.datetime.fromisoformat(msg.date.replace("Z", "+00:00"))

            if msg_time >= two_days_ago:
                if any(greet in msg.content.lower() for greet in GREETING_KEYWORDS):
                    logger.debug("Recent greeting found.")
                    return True
        except (ValueError, TypeError, AttributeError):
            # Ignore messages with malformed dates or content
            continue

    logger.debug("No greeting found in recent history.")
    return False
