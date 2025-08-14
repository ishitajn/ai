# tests/test_analysis_service.py

import pytest
from services.analysis_service import analyze_single_message
from api_models import ScrapedConversationMessage

def test_analyze_single_message_simple():
    """
    Tests that a simple, positive message is analyzed correctly.
    """
    message_text = "This is a great message!"
    role = "user"
    analysis = analyze_single_message(message_text, role, date=None)

    assert analysis.content == message_text
    assert analysis.role == role
    assert analysis.wordCount == 5
    assert analysis.subtext.valence > 0
    assert not analysis.questionInfo.isQuestion

def test_analyze_single_message_question():
    """
    Tests that a message ending with a question mark is identified as a question.
    """
    message_text = "What do you think?"
    role = "assistant"
    analysis = analyze_single_message(message_text, role, date=None)

    assert analysis.questionInfo.isQuestion
    assert analysis.questionInfo.type == "open"

def test_analyze_low_effort_message():
    """
    Tests that a common low-effort message is correctly identified.
    """
    message_text = "lol"
    role = "assistant"
    analysis = analyze_single_message(message_text, role, date=None)

    assert analysis.isLowEffort
