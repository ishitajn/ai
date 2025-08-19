import logging
from typing import Dict, Any, List

from analysis_models import FullConversationAnalysis
from api_models import (
    SummarizedAnalysis, ConversationSummary, LastMessageSummary, RecommendedActions, MemorySummary, ScrapedData
)
from constants import (
    SEMANTIC_HEATMAP_HOT_THRESHOLD, SEMANTIC_HEATMAP_MEDIUM_THRESHOLD,
    BASIC_HEATMAP_HOT_THRESHOLD, BASIC_HEATMAP_MEDIUM_THRESHOLD,
    SEMANTIC_FLIRT_LEVEL_HIGH_THRESHOLD, SEMANTIC_FLIRT_LEVEL_MEDIUM_THRESHOLD,
    BASIC_FLIRT_LEVEL_HIGH_THRESHOLD, BASIC_FLIRT_LEVEL_MEDIUM_THRESHOLD,
    SENTIMENT_SCORE_THRESHOLD, AROUSAL_SCORE_THRESHOLD,
    TOPIC_LIKED_THRESHOLD, TOPIC_DISLIKED_THRESHOLD
)
from .analysis.utils import get_dominant_topic, get_semantic_scores, score_to_heatmap, BASIC_TOPIC_KEYWORDS, TOPIC_DEFINITIONS, INTENT_DEFINITIONS

logger = logging.getLogger(__name__)

# --- Main Service Function ---
def summarize_analysis(
    full_analysis: FullConversationAnalysis,
    history: List[Dict[str, Any]],
    scraped_data: ScrapedData,
    analysis_engine: str,
    use_enhanced_nlp: bool,
) -> SummarizedAnalysis:
    """
    Transforms a detailed FullConversationAnalysis object into a concise,
    semantically-enhanced SummarizedAnalysis, respecting the NLP level.
    """
    logger.debug(f"Starting analysis summarization with enhanced_nlp={use_enhanced_nlp}.")

    last_message_analysis = full_analysis.lastMessageAnalysis
    conversation_text = " ".join([msg["content"].lower() for msg in history])

    # --- Conditional Analysis Path ---
    if use_enhanced_nlp:
        # ENHANCED: Use SentenceTransformer for semantic analysis
        topic_scores = get_semantic_scores(conversation_text, TOPIC_DEFINITIONS)
        topic_heatmap = {topic: score_to_heatmap(score) for topic, score in topic_scores.items()}
        flirtation_score = topic_scores.get("flirt", 0.0)
        dominant_topic = max(topic_scores, key=topic_scores.get) if topic_scores else "general"

        if last_message_analysis:
            intent_scores = get_semantic_scores(last_message_analysis.content, INTENT_DEFINITIONS)
            last_message_intent = max(intent_scores, key=intent_scores.get) if intent_scores else "statement"
        else:
            last_message_intent = "none"

    else:
        # BASIC: Use keyword matching for analysis
        conversation_words = set(conversation_text.split())
        topic_scores = {
            topic: sum(1 for keyword in keywords if keyword in conversation_words)
            for topic, keywords in BASIC_TOPIC_KEYWORDS.items()
        }
        topic_heatmap = {topic: "hot" if score > BASIC_HEATMAP_HOT_THRESHOLD else "medium" if score > BASIC_HEATMAP_MEDIUM_THRESHOLD else "low"
                         for topic, score in topic_scores.items()}
        flirtation_score = topic_scores.get("flirt", 0)
        dominant_topic = max(topic_scores, key=topic_scores.get) if any(topic_scores.values()) else "general"

        if last_message_analysis and last_message_analysis.questionInfo.isQuestion:
            last_message_intent = "question"
        else:
            last_message_intent = "statement"

    # --- Assemble Summary ---
    flirt_high_threshold = SEMANTIC_FLIRT_LEVEL_HIGH_THRESHOLD if use_enhanced_nlp else BASIC_FLIRT_LEVEL_HIGH_THRESHOLD
    flirt_med_threshold = SEMANTIC_FLIRT_LEVEL_MEDIUM_THRESHOLD if use_enhanced_nlp else BASIC_FLIRT_LEVEL_MEDIUM_THRESHOLD
    flirtation_level = "high" if flirtation_score > flirt_high_threshold else \
                       "medium" if flirtation_score > flirt_med_threshold else "low"

    # Use sentiment-based topic scores from memory for liked/disliked topics
    liked_topics = [topic for topic, details in full_analysis.memory.topics.items() if details.score > TOPIC_LIKED_THRESHOLD]
    disliked_topics = [topic for topic, details in full_analysis.memory.topics.items() if details.score < TOPIC_DISLIKED_THRESHOLD]

    # Analyze profile topics
    profile_text = scraped_data.theirProfile.lower()
    if use_enhanced_nlp:
        profile_topic_scores = get_semantic_scores(profile_text, TOPIC_DEFINITIONS)
        profile_topics = {topic: score_to_heatmap(score) for topic, score in profile_topic_scores.items()}
    else:
        profile_words = set(profile_text.split())
        profile_topic_scores = {
            topic: sum(1 for keyword in keywords if keyword in profile_words)
            for topic, keywords in BASIC_TOPIC_KEYWORDS.items()
        }
        profile_topics = {topic: "hot" if score > BASIC_HEATMAP_HOT_THRESHOLD else "medium" if score > BASIC_HEATMAP_MEDIUM_THRESHOLD else "low"
                          for topic, score in profile_topic_scores.items()}

    conversation_summary = ConversationSummary(
        is_engaged=full_analysis.conversationState == "ACTIVE_CONVO",
        conversation_stage=full_analysis.memory.dateArcPhase,
        topic_heatmap=topic_heatmap,
        liked_topics=liked_topics,
        disliked_topics=disliked_topics,
        reciprocity_balance="balanced",
        flirtation_level=flirtation_level,
        profile_topics=profile_topics,
        has_recent_greeting=not full_analysis.suppressGreeting,
        conversationState=full_analysis.conversationState,
        sexualResponseSuggestion=full_analysis.sexualAnalysis.sexualResponseSuggestion,
        isGeoRelated=last_message_analysis.isGeoRelated if last_message_analysis else False,
    )

    memory_summary = MemorySummary(
        insideJokes=full_analysis.memory.insideJokes,
        questionHistory=full_analysis.memory.questionHistory,
        kinksAndFetishes=full_analysis.sexualAnalysis.kinksAndFetishes,
        redFlags=full_analysis.memory.redFlags,
    )

    if last_message_analysis:
        last_message_topic = get_dominant_topic(last_message_analysis.content, use_enhanced_nlp)

        last_message = LastMessageSummary(
            sender=last_message_analysis.role,
            text=last_message_analysis.content,
            intent=last_message_intent,
            topic=last_message_topic,
            sentiment="positive" if last_message_analysis.subtext.valence > SENTIMENT_SCORE_THRESHOLD else "negative" if last_message_analysis.subtext.valence < -SENTIMENT_SCORE_THRESHOLD else "neutral",
            emotion="excited" if last_message_analysis.subtext.arousal > AROUSAL_SCORE_THRESHOLD else "calm",
            explicit="flirting_or_sexual" in last_message_analysis.subtext.intents,
            isQuestion=last_message_analysis.questionInfo.isQuestion,
            isGeoRelated=last_message_analysis.isGeoRelated,
        )
    else:
        last_message = LastMessageSummary(
            sender="none", text="", intent="none", topic="none",
            sentiment="none", emotion="none", explicit=False, isQuestion=False, isGeoRelated=False
        )

    suggestions = full_analysis.responseSuggestions

    # Suggest new topics from profile that haven't been discussed
    profile_hot_topics = {topic for topic, score in profile_topics.items() if score in ["hot", "medium"]}
    convo_hot_topics = {topic for topic, score in topic_heatmap.items() if score in ["hot", "medium"]}
    new_topic_suggestions = list(profile_hot_topics - convo_hot_topics)

    recommended_actions = RecommendedActions(
        focus_topic=dominant_topic,
        ask_question_back=suggestions.endWithQuestion,
        escalate_flirtation=flirtation_level != "high",
        next_topic_suggestion=new_topic_suggestions,
        isVirtual=full_analysis.geoContext.isVirtual,
        avoid_repeating_user=False,
        length=suggestions.length,
        tone=suggestions.tone,
        linguisticStyle=suggestions.linguisticStyle,
        emojiStrategy=suggestions.emojiStrategy,
        endWithQuestion=suggestions.endWithQuestion,
        suggestedNextAction=suggestions.suggestedNextAction,
        analysisEngine=analysis_engine,
        sexualCommunicationStyle=full_analysis.sexualAnalysis.sexualCommunicationStyle,
        dateArcPhase=full_analysis.memory.dateArcPhase,
        suggestedResponseStyle=last_message_analysis.suggestedResponseStyle if last_message_analysis else "casual",
    )

    return SummarizedAnalysis(
        conversation_summary=conversation_summary,
        last_message=last_message,
        recommended_actions=recommended_actions,
        memory_summary=memory_summary,
        geoContext=full_analysis.geoContext,
    )
