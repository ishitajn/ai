import logging
from typing import Dict, Any, List
from sentence_transformers import SentenceTransformer, util

from analysis_models import FullConversationAnalysis
from api_models import SummarizedAnalysis, ConversationSummary, LastMessageSummary, RecommendedActions

logger = logging.getLogger(__name__)

# --- Model Loading ---
# Load the SentenceTransformer model once when the module is loaded.
logger.info("Loading SentenceTransformer model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
logger.info("SentenceTransformer model loaded successfully.")

# --- Semantic Definitions ---
TOPIC_DEFINITIONS = {
    "travel": ["going on a trip", "visiting new places", "exploring the world", "booking a flight"],
    "food": ["what's your favorite restaurant", "I love cooking", "trying new cuisines", "are you a foodie"],
    "flirt": ["you have beautiful eyes", "I can't stop thinking about you", "you're really cute", "sending you a kiss"],
    "sexual": ["I want you so bad", "can't wait to get you in bed", "thinking about your body"],
    "sports": ["did you watch the game last night", "I love playing soccer", "who's your favorite team"],
    "career": ["what do you do for work", "I'm a software engineer", "my job is very demanding"],
}

INTENT_DEFINITIONS = {
    "question": ["what are you doing?", "how are you?", "can you tell me more?", "are you free?"],
    "statement": ["that's interesting", "I agree with you", "I went to the store today"],
    "planning": ["let's meet up tomorrow", "what time works for you?", "are you free on friday?"],
    "joke": ["that's hilarious", "you're so funny", "I was just kidding"],
    "opinion": ["I think that's a great idea", "in my opinion, that's not right"],
}

# --- Helper Functions ---
def get_semantic_scores(text: str, definitions: Dict[str, List[str]]) -> Dict[str, float]:
    if not text:
        return {key: 0.0 for key in definitions.keys()}

    text_embedding = model.encode(text, convert_to_tensor=True)
    scores = {}

    for key, examples in definitions.items():
        example_embeddings = model.encode(examples, convert_to_tensor=True)
        cosine_scores = util.pytorch_cos_sim(text_embedding, example_embeddings)
        scores[key] = cosine_scores.max().item()

    return scores

def score_to_heatmap(score: float) -> str:
    if score > 0.6: return "hot"
    if score > 0.35: return "medium"
    return "low"

# --- Main Service Function ---
def summarize_analysis(
    full_analysis: FullConversationAnalysis,
    history: List[Dict[str, Any]]
) -> SummarizedAnalysis:
    """
    Transforms a detailed FullConversationAnalysis object into a concise,
    semantically-enhanced SummarizedAnalysis.
    """
    logger.debug("Starting analysis summarization.")

    conversation_text = " ".join([msg["content"] for msg in history])
    topic_scores = get_semantic_scores(conversation_text, TOPIC_DEFINITIONS)

    flirtation_score = topic_scores.get("flirt", 0.0)
    flirtation_level = "high" if flirtation_score > 0.5 else "medium" if flirtation_score > 0.25 else "low"

    conversation_summary = ConversationSummary(
        is_engaged=full_analysis.conversationState == "ACTIVE_CONVO",
        conversation_stage=full_analysis.memory.dateArcPhase,
        topic_heatmap={topic: score_to_heatmap(score) for topic, score in topic_scores.items()},
        liked_topics=[topic for topic, score in topic_scores.items() if score > 0.35],
        disliked_topics=[],  # Low score doesn't mean dislike, this is a harder problem.
        reciprocity_balance="balanced", # Placeholder
        flirtation_level=flirtation_level,
        profile_topics={}, # Placeholder
        has_recent_greeting=not full_analysis.suppressGreeting,
    )

    last_message_analysis = full_analysis.lastMessageAnalysis
    if last_message_analysis:
        intent_scores = get_semantic_scores(last_message_analysis.content, INTENT_DEFINITIONS)
        last_message_intent = max(intent_scores, key=intent_scores.get) if intent_scores else "statement"

        last_message = LastMessageSummary(
            sender=last_message_analysis.role,
            text=last_message_analysis.content,
            intent=last_message_intent,
            topic=max(topic_scores, key=topic_scores.get) if topic_scores else "general",
            sentiment= "positive" if last_message_analysis.subtext.valence > 0.1 else "negative" if last_message_analysis.subtext.valence < -0.1 else "neutral",
            emotion="excited" if last_message_analysis.subtext.arousal > 0.1 else "calm",
            explicit="flirting_or_sexual" in last_message_analysis.subtext.intents,
            isQuestion=last_message_analysis.questionInfo.isQuestion,
        )
    else:
        last_message = LastMessageSummary(
            sender="none", text="", intent="none", topic="none",
            sentiment="none", emotion="none", explicit=False, isQuestion=False
        )

    recommended_actions = RecommendedActions(
        focus_topic=max(topic_scores, key=topic_scores.get) if topic_scores else "rapport",
        ask_question_back=full_analysis.responseSuggestions.endWithQuestion,
        escalate_flirtation=flirtation_level != "high", # Suggest escalation if not already high
        next_topic_suggestion=[], # Placeholder
        isVirtual=full_analysis.geoContext.isVirtual,
        avoid_repeating_user=False # Placeholder
    )

    summary = SummarizedAnalysis(
        conversation_summary=conversation_summary,
        last_message=last_message,
        recommended_actions=recommended_actions,
    )

    logger.debug("Finished analysis summarization.")
    return summary
