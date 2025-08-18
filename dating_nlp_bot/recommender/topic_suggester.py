def suggest_topics(analyzed_topics):
    """
    Suggests next topics based on the analyzed topic data.
    This is a simple rule-based suggester.
    """
    next_topic = "life goals" # A safe, open-ended default
    avoid_topic = "past relationships" # Usually a good idea to avoid early on
    escalate_topic = ""

    liked_topics = analyzed_topics.get("liked", [])
    neutral_topics = analyzed_topics.get("neutral", [])
    sensitive_topics = analyzed_topics.get("sensitive", [])

    # If flirtation or sexual topics are present and not disliked, suggest escalation
    if "flirt" in neutral_topics or "flirt" in liked_topics or "sexual" in sensitive_topics:
        escalate_topic = "sexual chemistry"

    # Suggest a new, interesting topic
    potential_next = ["travel", "hobbies", "career", "food", "movies"]
    all_discussed = set(liked_topics + neutral_topics)

    for p in potential_next:
        if p not in all_discussed:
            next_topic = p
            break

    # Avoid sensitive topics if they haven't been brought up
    if not sensitive_topics:
        avoid_topic = "anything too sexual or intense"

    return {
        "next_topic": next_topic,
        "avoid_topic": avoid_topic,
        "escalate_topic": escalate_topic
    }
