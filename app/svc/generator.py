from app.schemas import Suggestions, FeatureProbes, Topic, Geo
from typing import List
import random
import asyncio

async def suggest(features: FeatureProbes, topics: List[Topic], geo: Geo) -> Suggestions:
    """
    Generates context-aware suggestions. Mocking a non-blocking LLM call.
    """
    # Simulate a non-blocking I/O call (e.g., to a remote LLM)
    await asyncio.sleep(0.02)

    suggestions = Suggestions()

    # 1. Address direct questions from the match
    if features.match_contains_question:
        suggestions.topics.append("They just asked a question, it would be good to answer it.")

    # 2. Generate topic-based suggestions from focused topics
    focus_topics = [t for t in topics if t.category == 'focus']
    if focus_topics:
        chosen_topic = random.choice(focus_topics)
        suggestions.topics.append(f"You were just talking about {chosen_topic.label.lower()}. Maybe ask what they think about it?")
        if chosen_topic.keywords:
            suggestions.questions.append(f"What's your favorite thing about {chosen_topic.keywords[0]}?")

    # 3. Handle Flirtation and Intimacy
    if features.flirtation_detected and features.reciprocity:
        suggestions.sexual.append("The energy is getting flirty! Try giving a compliment about their personality or humor.")
    elif features.playful_energy:
        suggestions.topics.append("The vibe is playful. Share a funny story or a meme.")

    # 4. Late-night context from the new Geo object
    if geo.userLocation.timeOfDay in ["Evening", "Night"] and features.disclosure:
        suggestions.intimacy.append("It's getting late and you're both opening up. Maybe ask about their evening routine or a favorite late-night snack.")

    # 5. Default suggestion if no other context fits
    if not suggestions.topics and not suggestions.questions:
        suggestions.questions.append("Ask them about something they are passionate about.")
        neutral_topics = [t for t in topics if t.category == 'neutral' and t.label != "General Chat"]
        if neutral_topics:
            suggestions.topics.append(f"You could pivot back to talking about {random.choice(neutral_topics).label.lower()}.")

    return suggestions
