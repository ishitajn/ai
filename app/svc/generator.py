from app.schemas import ContextPack, Suggestions, Topic
import random

def suggest(context: ContextPack) -> Suggestions:
    """
    Generates context-aware suggestions.
    This is a mock implementation of the Tiny LLM's role, using rule-based logic.
    """
    suggestions = Suggestions()
    features = context.features
    topics = context.topics

    # --- Rule-based suggestion generation based on context ---

    # 1. Address direct questions first
    if features.questions:
        suggestions.talking_points.append("They just asked a question. It's a good idea to answer it directly.")

    # 2. Generate topic-based talking points
    if topics:
        chosen_topic = random.choice(topics)
        if chosen_topic.label != "General Chat":
            suggestions.talking_points.append(f"You were talking about {chosen_topic.label.lower()}. You could share your thoughts on it.")
            if chosen_topic.keywords:
                suggestions.questions.append(f"What's your take on {chosen_topic.keywords[0]}?")

    # 3. Handle Flirtation, Sexual, and Intimacy suggestions
    # Escalation readiness is not yet computed, so we use reciprocity and energy as proxies.
    if features.flirtation_detected and features.reciprocity:
        suggestions.sexual_suggestions.append("The energy is getting flirty! Try giving a specific, genuine compliment.")
        suggestions.next_action_plans.append("Maybe it's time to suggest moving the conversation to a more private chat or a call.")
    elif features.playful_energy:
        suggestions.talking_points.append("The vibe is playful. Share a funny story or ask about a light-hearted topic.")

    # 4. Context-aware intimacy suggestions based on time
    if context.geo.time_of_day in ["evening", "night"] and features.disclosure:
        suggestions.intimacy_suggestions.append("It's getting late and you're both opening up. Ask about their evening routine or a favorite late-night snack.")

    # 5. Default suggestion if no other context fits
    if not suggestions.talking_points and not suggestions.questions:
        suggestions.questions.append("Ask them about something they're passionate about.")
        suggestions.questions.append("What's the best part of their week been so far?")

    return suggestions
