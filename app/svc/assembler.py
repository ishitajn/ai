from app.schemas import (
    Payload, Topic, Geo, Suggestions, FeatureProbes,
    UnifiedJSONOutput, ConversationState, ConversationStateTopics,
    Analysis, LastMatchResponse, Sentiment
)
from typing import List

def _build_conversation_state(topics: List[Topic]) -> ConversationState:
    """Sorts the categorized topics into the ConversationState object."""
    state_topics = ConversationStateTopics()
    recent_labels = []

    for topic in topics:
        recent_labels.append(topic.label)
        if topic.category == 'focus':
            state_topics.focus.append(topic.label)
        elif topic.category == 'avoid':
            state_topics.avoid.append(topic.label)
        elif topic.category == 'sensitive':
            state_topics.sensitive.append(topic.label)
        elif topic.category == 'fetish':
            state_topics.fetish.append(topic.label)
        elif topic.category == 'sexual':
            state_topics.sexual.append(topic.label)
        else: # neutral
            state_topics.neutral.append(topic.label)

    return ConversationState(topics=state_topics, recent_topics=recent_labels[-5:])

def _build_analysis(features: FeatureProbes) -> Analysis:
    """
    Builds the detailed Analysis object from raw feature probes.
    This uses heuristics to fill in the more interpretive fields.
    """
    # Engagement level
    engagement_score = 0
    if features.reciprocity: engagement_score += 2
    if features.disclosure: engagement_score += 1
    if features.response_length_class == 'high': engagement_score += 1
    if features.response_length_class == 'low': engagement_score -= 1

    match_engaged = "low"
    if engagement_score >= 3: match_engaged = "high"
    elif engagement_score >= 1: match_engaged = "medium"

    # Comfort and Escalation
    comfort_level = "low"
    if features.disclosure: comfort_level = "medium"
    if features.disclosure and features.playful_energy: comfort_level = "high"

    escalation_readiness = "early"
    if comfort_level == "medium" and features.flirtation_detected: escalation_readiness = "moderate"
    if comfort_level == "high" and features.flirtation_detected: escalation_readiness = "ready"

    # Flirtation level
    flirtation_level = "none"
    if features.flirtation_detected: flirtation_level = "low"
    if features.flirtation_detected and features.playful_energy: flirtation_level = "medium"

    return Analysis(
        last_response=features.last_response_by,
        last_match_response=LastMatchResponse(
            contains_question=features.match_contains_question,
            related_to_location=features.location_related
        ),
        match_engaged=match_engaged,
        comfort_level=comfort_level,
        escalation_readiness=escalation_readiness,
        recent_greeting_used=features.recent_greeting_used,
        flirtation_level=flirtation_level,
        sexual_response_allowed=(escalation_readiness == "ready" and flirtation_level == "medium"),
        # --- Defaulted values for highly interpretive fields ---
        conversation_pace="balanced",
        reciprocity_balance="balanced",
        length=80,
        tone=60,
        linguistic_style="casual",
        emoji_strategy="auto",
        suggested_next_action="MAINTAIN_ENGAGEMENT",
        sexual_communication_style="casual_and_flirty",
        date_arc_phase="rapport_building",
        suggested_response_style="thoughtful"
    )

def _build_sentiment(features: FeatureProbes) -> Sentiment:
    """Builds a simple sentiment object. Mock implementation."""
    if features.playful_energy or features.flirtation_detected:
        return Sentiment(overall="positive")
    return Sentiment(overall="neutral")

def build(
    payload: Payload,
    topics: List[Topic],
    geo: Geo,
    suggestions: Suggestions,
    features: FeatureProbes
) -> UnifiedJSONOutput:
    """
    Merges all outputs from the services into the final, detailed JSON schema.
    """
    conversation_state = _build_conversation_state(topics)
    analysis = _build_analysis(features)
    sentiment = _build_sentiment(features)

    return UnifiedJSONOutput(
        matchId=payload.match_profile.match_id,
        conversation_state=conversation_state,
        geo=geo,
        suggestions=suggestions,
        analysis=analysis,
        sentiment=sentiment,
        pipeline="enhanced_mock_v1"
    )
