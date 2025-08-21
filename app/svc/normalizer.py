import re
from app.schemas import Payload, NormalizedData, Message
from typing import List

CONTEXT_SIZE_LIMIT = 15

def clean_text(text: str) -> str:
    """Removes noise and trims messages."""
    # A simple regex to remove extra whitespace and strip the message
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean(payload: Payload) -> NormalizedData:
    """
    Cleans and normalizes the conversation history.
    - Removes noise from messages.
    - Trims messages.
    - Limits context size to avoid token overflow.
    """
    history = payload.conversation_history

    # Clean each message's text
    cleaned_turns: List[Message] = []
    for msg in history:
        cleaned_text = clean_text(msg.text)
        if cleaned_text:  # Only keep non-empty messages
            cleaned_turns.append(
                Message(
                    role=msg.role,
                    text=cleaned_text,
                    timestamp=msg.timestamp
                )
            )

    # Truncate to the last N turns
    truncated_turns = cleaned_turns[-CONTEXT_SIZE_LIMIT:]

    was_truncated = len(cleaned_turns) > CONTEXT_SIZE_LIMIT

    return NormalizedData(
        turns=truncated_turns,
        truncated_history=was_truncated
    )
