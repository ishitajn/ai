from datetime import datetime

def analyze_conversation_dynamics_fast(conversation_history):
    """
    Analyzes conversation dynamics using rule-based heuristics.
    """
    if not conversation_history:
        return {
            "question_detected": False, "recent_greeting": False, "pace": "balanced",
            "stage": "starting", "is_engaged": False, "reciprocity_balance": "balanced",
            "flirtation_level": "low", "sexualResponseSuggestion": False
        }

    question_detected = any("?" in msg['content'] for msg in conversation_history)

    first_message = conversation_history[0]['content'].lower()
    recent_greeting = any(greeting in first_message for greeting in ['hey', 'hi', 'hello'])

    # Pace calculation
    pace = "balanced"
    if len(conversation_history) > 1:
        try:
            first_date = datetime.strptime(conversation_history[0]['date'], "%Y-%m-%d")
            last_date = datetime.strptime(conversation_history[-1]['date'], "%Y-%m-%d")
            duration_days = (last_date - first_date).days + 1
            messages_per_day = len(conversation_history) / duration_days if duration_days > 0 else len(conversation_history)
            if messages_per_day > 10:
                pace = "fast"
            elif messages_per_day < 2:
                pace = "slow"
        except (ValueError, TypeError):
            pace = "balanced" # Default on date parsing error

    # Stage calculation
    stage = "active"
    try:
        last_message_date = datetime.strptime(conversation_history[-1]['date'], "%Y-%m-%d")
        days_since_last_message = (datetime.now() - last_message_date).days
        if days_since_last_message > 30:
            stage = "break_over_month"
        elif days_since_last_message > 7:
            stage = "break_1_week"
        elif days_since_last_message > 2:
            stage = "break_2_days"
    except (ValueError, TypeError):
        stage = "active"

    # Reciprocity
    user_messages = sum(1 for msg in conversation_history if msg['role'] == 'user')
    match_messages = sum(1 for msg in conversation_history if msg['role'] == 'assistant')
    reciprocity_balance = "balanced"
    if user_messages > match_messages * 1.5:
        reciprocity_balance = "user_dominant"
    elif match_messages > user_messages * 1.5:
        reciprocity_balance = "match_dominant"

    is_engaged = stage == "active" and pace != "slow"

    # These would require more complex analysis, simplified here
    flirtation_level = "low"
    sexual_response_suggestion = False

    return {
        "question_detected": question_detected,
        "recent_greeting": recent_greeting,
        "pace": pace,
        "stage": stage,
        "is_engaged": is_engaged,
        "reciprocity_balance": reciprocity_balance,
        "flirtation_level": flirtation_level,
        "sexualResponseSuggestion": sexual_response_suggestion
    }

def analyze_conversation_dynamics_enhanced(conversation_history, model_name=None):
    """
    For now, enhanced dynamics analysis falls back to the fast version.
    A true enhanced version might use a classifier to predict engagement or stage.
    """
    return analyze_conversation_dynamics_fast(conversation_history)

def analyze_conversation_dynamics(conversation_history, use_enhanced_nlp, model_name=None):
    if use_enhanced_nlp:
        # This could be a more advanced implementation in the future
        return analyze_conversation_dynamics_enhanced(conversation_history, model_name)
    else:
        return analyze_conversation_dynamics_fast(conversation_history)
