from datetime import datetime, timedelta

def analyze_response(conversation_history):
    """
    Analyzes the last user and match responses.
    """
    last_match_response = {"contains_question": False, "related_to_location": False}
    last_user_response_24h = {"sent_greeting": False, "sexual_escalation": False}

    if not conversation_history:
        return {
            "last_match_response": last_match_response,
            "last_user_response_24h": last_user_response_24h
        }

    # Find the last message from the match ('assistant')
    for msg in reversed(conversation_history):
        if msg['role'] == 'assistant':
            content = msg['content'].lower()
            last_match_response["contains_question"] = "?" in content
            if any(loc_word in content for loc_word in ['live', 'place', 'area', 'location', 'city', 'country']):
                last_match_response["related_to_location"] = True
            break

    # Find user responses in the last 24 hours
    one_day_ago = datetime.now() - timedelta(days=1)
    for msg in reversed(conversation_history):
        try:
            msg_date = datetime.strptime(msg['date'], "%Y-%m-%d")
            if msg['role'] == 'user' and msg_date >= one_day_ago:
                content = msg['content'].lower()
                if any(greeting in content for greeting in ['hey', 'hi', 'hello']):
                    last_user_response_24h["sent_greeting"] = True
                if any(word in content for word in ['sex', 'naked', 'bed', 'intimate']):
                     last_user_response_24h["sexual_escalation"] = True
        except (ValueError, TypeError):
            continue # Skip messages with invalid dates

    return {
        "last_match_response": last_match_response,
        "last_user_response_24h": last_user_response_24h
    }
