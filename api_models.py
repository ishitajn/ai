from pydantic import BaseModel, Field
from typing import List, Optional, Dict

from analysis_models import (
    MessageAnalysis, MatchMemory, DateAnalysis,
    SexualAnalysis, ResponseSuggestions, GeoContext
)

# --- API Request Payloads ---

class ScrapedConversationMessage(BaseModel):
    role: str
    content: str
    date: Optional[str] = None

class ScrapedData(BaseModel):
    myName: Optional[str] = "You"
    theirName: Optional[str] = "Match"
    theirProfile: str
    theirLocationString: Optional[str] = None
    conversationHistory: List[ScrapedConversationMessage]

class UISettings(BaseModel):
    """
    The settings required for an analysis. Consolidates previous Initial and Full models.
    """
    myLocation: str
    myProfile: str
    local_model_name: Optional[str] = None # Made optional as it may not be relevant
    useEnhancedNlp: bool = Field(default=False)
    # Optional overrides can be added here if ever needed again

class AnalysisRequest(BaseModel):
    """Payload for the /analyze endpoint."""
    matchId: str
    scraped_data: ScrapedData
    ui_settings: UISettings


# --- API Response Model ---

class FrontendAnalysisResponse(BaseModel):
    """
    The single, comprehensive response object that provides the specific
    fields required by the frontend.
    """
    conversationState: str
    suppressGreeting: bool
    lastMessageAnalysis: Optional[MessageAnalysis]
    memory: MatchMemory
    dateAnalysis: DateAnalysis
    sexualAnalysis: SexualAnalysis
    responseSuggestions: ResponseSuggestions
    geoContext: GeoContext
    analysisEngine: str = Field(..., description="The analysis engine used for the request, e.g., 'legacy_keyword' or 'enhanced_vader'.")



# --- Summarized Analysis Models ---

class ConversationSummary(BaseModel):
    is_engaged: bool
    conversation_stage: str
    topic_heatmap: Dict[str, str]
    liked_topics: List[str]
    disliked_topics: List[str]
    reciprocity_balance: str
    flirtation_level: str
    profile_topics: Dict[str, str]
    has_recent_greeting: bool

class LastMessageSummary(BaseModel):
    sender: str
    text: str
    intent: str
    topic: str
    sentiment: str
    emotion: str
    explicit: bool
    isQuestion: bool

class RecommendedActions(BaseModel):
    focus_topic: str
    ask_question_back: bool
    escalate_flirtation: bool
    next_topic_suggestion: List[str]
    isVirtual: bool
    avoid_repeating_user: bool

class SummarizedAnalysis(BaseModel):
    conversation_summary: ConversationSummary
    last_message: LastMessageSummary
    recommended_actions: RecommendedActions
