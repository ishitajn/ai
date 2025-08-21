from app.schemas import (
    Payload, Topic, GeoTimeInfo, Suggestions, FeatureProbes,
    UnifiedJSONOutput, Analysis, SexualIntimacyAnalysis, EngagementMetrics
)
from typing import List

def _build_engagement_metrics(features: FeatureProbes) -> EngagementMetrics:
    """Builds the EngagementMetrics from feature probes."""
    indicators = []
    score = 0

    if features.reciprocity:
        indicators.append("Reciprocated conversation")
        score += 1
    if features.disclosure:
        indicators.append("Personal disclosure")
        score += 1
    if features.question_asking:
        indicators.append("User asked questions")
        score += 1
    if features.response_length_class == "high":
        score += 1
    elif features.response_length_class == "low":
        score -= 1

    level = "low"
    if score >= 3:
        level = "high"
    elif score >= 1:
        level = "medium"

    return EngagementMetrics(
        level=level,
        indicators=indicators,
        reciprocity=features.reciprocity,
        disclosure=features.disclosure,
        question_asking=features.question_asking,
        response_length_class=features.response_length_class
    )

def _build_sexual_intimacy_analysis(features: FeatureProbes) -> SexualIntimacyAnalysis:
    """Builds the SexualIntimacyAnalysis from feature probes."""
    comfort = "low"
    readiness = "early"

    if features.disclosure and features.reciprocity:
        comfort = "medium"
        if features.playful_energy:
            comfort = "high"

    if comfort == "medium" and features.flirtation_detected:
        readiness = "moderate"
    if comfort == "high" and features.flirtation_detected and features.reciprocity:
        readiness = "ready"

    return SexualIntimacyAnalysis(
        flirtation_detected=features.flirtation_detected,
        sexual_tone=features.sexual_tone,
        playful_energy=features.playful_energy,
        comfort_level=comfort,
        escalation_readiness=readiness
    )

def build(
    payload: Payload,
    topics: List[Topic],
    geo: GeoTimeInfo,
    suggestions: Suggestions,
    features: FeatureProbes
) -> UnifiedJSONOutput:
    """
    Merges all outputs into the final JSON schema.
    """
    engagement = _build_engagement_metrics(features)
    sexual_intimacy = _build_sexual_intimacy_analysis(features)

    analysis = Analysis(
        sexual_intimacy=sexual_intimacy,
        engagement=engagement
    )

    return UnifiedJSONOutput(
        topics=topics,
        geo=geo,
        predictions_and_suggestions=suggestions,
        analysis=analysis
    )
