from pydantic import BaseModel, Field
from typing import List, Optional

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
